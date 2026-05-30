# Wachturm — Architecture

This document describes how Wachturm fits together: the container topology, the network model, the data flow, and the rationale behind each tool choice. It's the source of truth for *what goes where and why*.

## 1. Big picture

```
┌────────────────────────────────────────────────────────────────────────┐
│                              WACHTURM                                  │
│                                                                        │
│  ┌─────────────────┐      ┌───────────────────┐     ┌───────────────┐  │
│  │   Attackers     │─────▶│      Victims      │────▶│   Detection   │  │
│  │   (scripted)    │      │ (Linux + fake Win │     │     Layer     │  │
│  │   atk-*         │      │  logs via syslog) │     │               │  │
│  └─────────────────┘      │  vic-web          │     │  wazuh-mgr    │  │
│                           │  vic-work         │     │  wazuh-idx    │  │
│  ┌─────────────────┐      │  vic-jump         │     │  wazuh-dash   │  │
│  │  Benign Noise   │─────▶│  vic-dc (fake AD) │     │  suricata     │  │
│  │  generator      │      └───────────────────┘     └───────┬───────┘  │
│  │  noise-gen      │                                        │          │
│  └─────────────────┘                                        │          │
│                                                             ▼          │
│                                       ┌────────────────────────────┐   │
│                                       │   Case Management Layer    │   │
│                                       │                            │   │
│                                       │   iris     ◀──▶  cortex    │   │
│                                       │       ▲             ▲      │   │
│                                       │       │             │      │   │
│                                       └───────┼─────────────┼──────┘   │
│                                               │             │          │
│                                               ▼             ▼          │
│                                       ┌──────────────────────────┐     │
│                                       │   SOAR + Threat Intel    │     │
│                                       │                          │     │
│                                       │   shuffle    misp        │     │
│                                       └──────────────────────────┘     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Container inventory

| Container | Role | Profile | Approx. RAM |
|---|---|---|---|
| `wazuh-manager` | Wazuh manager (rule engine, agent connect) | core | 1.5 GB |
| `wazuh-indexer` | OpenSearch backend for Wazuh | core | 2 GB |
| `wazuh-dashboard` | Wazuh web UI | core | 0.5 GB |
| `vic-web` | Victim: nginx web server with Wazuh agent | core | 0.3 GB |
| `vic-work` | Victim: Ubuntu "workstation" with Wazuh agent | core | 0.4 GB |
| `vic-jump` | Victim: SSH jumpbox with Wazuh agent | core | 0.3 GB |
| `vic-dc` | Victim: fake "Domain Controller" emitting Windows-style logs | core | 0.3 GB |
| `atk-kali` | Attacker: minimal Kali-like toolkit (nmap, hydra, curl, atomic-red-team) | core | 0.3 GB |
| `noise-gen` | Benign activity generator (Python) | core | 0.2 GB |
| `wachturm-portal` | Landing page + health proxy (nginx) | core | 0.05 GB |
| `suricata` | NIDS, EVE JSON output to Wazuh | core | 0.6 GB |
| `iris-db` | PostgreSQL for DFIR-IRIS | casemgmt | 0.4 GB |
| `iris-rabbitmq` | Message bus for DFIR-IRIS workers | casemgmt | 0.2 GB |
| `iris-worker` | DFIR-IRIS background worker | casemgmt | 0.4 GB |
| `iris-app` | DFIR-IRIS web application | casemgmt | 0.6 GB |
| `iris-nginx` | nginx reverse proxy in front of IRIS | casemgmt | 0.05 GB |
| `cortex-es` | Elasticsearch for Cortex (still required) | casemgmt | 1 GB |
| `cortex` | Cortex analyzer engine | casemgmt | 0.8 GB |
| `shuffle-frontend` | Shuffle UI | soar | 0.4 GB |
| `shuffle-backend` | Shuffle backend | soar | 0.5 GB |
| `shuffle-orborus` | Shuffle worker orchestrator | soar | 0.3 GB |
| `misp` | MISP threat intel platform | intel | 1.5 GB |
| `misp-db` | MariaDB for MISP | intel | 0.5 GB |

**Profile budgets:**
- `core` only: ~6.5 GB → fits on an 8 GB laptop with care
- `core + casemgmt`: ~10 GB → comfortable on 16 GB (IRIS + PostgreSQL is lighter than the old TheHive + Cassandra + Elasticsearch stack)
- `core + casemgmt + soar`: ~11.5 GB → comfortable on 16 GB
- `full` (all profiles): ~14 GB → 24 GB recommended

## 3. Network model

Three Docker networks, all `bridge` driver, all internal where possible.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   wachturm-victims  (10.50.10.0/24)                             │
│   ──────────────────────────────────                            │
│     vic-web, vic-work, vic-jump, vic-dc, noise-gen              │
│                                                                 │
│   wachturm-attack   (10.50.20.0/24)                             │
│   ──────────────────────────────────                            │
│     atk-kali  +  (gateway routed to wachturm-victims only)      │
│     ⚠ NO default route to host or internet                      │
│                                                                 │
│   wachturm-mgmt     (10.50.30.0/24)                             │
│   ──────────────────────────────────                            │
│     wazuh-*, iris-*, cortex, shuffle*, misp*, suricata        │
│     + can reach wachturm-victims for agent collection           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

Connectivity rules:
- Victims can talk to each other (lateral movement scenarios need this).
- Attackers can reach victims, but not the mgmt network or the host.
- Mgmt can reach victims (for log collection, agent enrollment).
- Mgmt cannot initiate to attackers.
- Only the Wazuh dashboard, DFIR-IRIS, Cortex, Shuffle, and MISP UIs are bound to `127.0.0.1` on the host for the student to access via browser.

**Egress policy:** the inviolable rule is that the **attacker** has no egress. `wachturm-attack` and `wachturm-victims` are `internal: true` — no NAT route to host or internet; `atk-kali` is dual-homed onto `victims` so it still reaches victim hosts but has no way off-box (AGENTS §6.2, the hard rule). `wachturm-mgmt` is **not** `internal`: it hosts the student-facing UIs (Wazuh dashboard, portal, and later IRIS/Cortex/MISP) that §7 requires reachable at `127.0.0.1` — `internal: true` makes host-port publishing inert (Docker cannot bridge the host to a container that lives only on an internal network), which would make the lab unusable. mgmt UIs are loopback-only ingress (§6.1); mgmt *egress* is accepted and is where the Cortex VT/AbuseIPDB enrichment exception lives. Sealing mgmt is **not** required for the security model — sealing the attacker is, and that is preserved.

## 4. Data flow — the happy path

A true positive walks through the stack like this:

1. **Attack runs.** `atk-kali` executes a scenario step, e.g. `hydra -l admin -P wordlist ssh://vic-jump`.
2. **Victim generates logs.** `vic-jump`'s `/var/log/auth.log` records the failed and eventually successful SSH attempts.
3. **Wazuh agent ships logs.** The agent on `vic-jump` ships them to `wazuh-manager`.
4. **Wazuh rule fires.** Rule 5712 (multi-failed-SSH) and rule 5715 (successful login after failures) fire on the manager.
5. **Alert in dashboard.** Visible in the Wazuh dashboard at `https://localhost:5601` (or whatever port).
6. **Integration to DFIR-IRIS.** Wazuh integration script POSTs the alert to DFIR-IRIS, which auto-creates a case with observables (src IP, user, host).
7. **Cortex enrichment.** Either auto-triggered or analyst-triggered, Cortex runs analyzers on the observables (e.g., AbuseIPDB lookup of source IP).
8. **MISP correlation.** Cortex queries MISP for IoC matches.
9. **Shuffle playbook (optional).** A playbook may auto-tag the case, post a mock notification, or close obvious FPs.
10. **Analyst (student) triages.** Investigates, sets verdict, writes a summary, closes the case.
11. **Scoring.** A `wachturm score` command reads the closed case from DFIR-IRIS's API and compares to the scenario's answer key.

## 5. Per-tool rationale

### Wazuh (SIEM + HIDS + EDR-lite)
Why: one tool covers three roles, which keeps the learning curve manageable. Wazuh ships rules out of the box, ingests Suricata EVE JSON natively, has agents for Linux, and the dashboard is approachable. The alternative (Elastic Stack + Beats + custom rules) is more industry-common but ~3x the setup complexity.

Tradeoff: students won't see Wazuh in most real SOC jobs. Mitigation: emphasize that the *workflow* (alert → triage → enrich → escalate) transfers to any SIEM.

### Suricata (NIDS)
Why: lightweight, EVE JSON output is widely supported, Wazuh has first-class integration. We skip Zeek for v1 to keep the log-format count down.

### DFIR-IRIS (case management)
Why: open-source under LGPL3, Docker-native, actively maintained. Replaces TheHive 5, which moved to a non-open-source freemium model at the end of 2022. The IR consulting community migrated heavily to IRIS after that change, so students who learn IRIS will increasingly see it in real IR consultancy job ads. PostgreSQL-backed (single database) vs. TheHive's Cassandra + Elasticsearch stack, which saves ~3 GB RAM.

Tradeoff: IRIS has less polished UI than TheHive and less learning material exists online. The workflow concepts (cases, observables, IOCs, timeline) transfer to any IR platform; the screens won't match a student's eventual employer exactly. Acceptable cost for the open-source guarantee.

### Cortex (observable enrichment)
Why: still the standard for analyzer-based IoC enrichment. Open source under AGPLv3, stable, well-documented. IRIS has its own module ecosystem that overlaps with Cortex; Wachturm uses both — Cortex for the "run an analyzer on this IP" workflow, IRIS modules for case-management-side automation.

### Shuffle (SOAR)
Why: open-source, visual playbook editor good for teaching, native integrations with IRIS, TheHive APIs (for downstream compatibility), and Cortex. Skip n8n — too generic and not security-shaped.

### MISP (threat intel)
Why: the standard. Even if students never run MISP in their first job, every threat intel platform borrows MISP's vocabulary (events, attributes, IoCs, galaxies).

### Atomic Red Team (attack simulation)
Why: don't reinvent. 1500+ tests mapped to MITRE ATT&CK. We don't run Atomic Red Team directly — we wrap selected tests in our scenario format.

## 6. Persistence and volumes

| Volume | Mounted by | Purpose | Persistent? |
|---|---|---|---|
| `wazuh-mgr-config` | wazuh-manager | rules, decoders, agent keys | yes |
| `wazuh-mgr-logs` | wazuh-manager | alerts.json archive | yes |
| `wazuh-idx-data` | wazuh-indexer | OpenSearch indices | yes |
| `iris-db-data` | iris-db | PostgreSQL data for IRIS | yes |
| `iris-rabbitmq-data` | iris-rabbitmq | RabbitMQ queue state | yes |
| `iris-app-data` | iris-app | IRIS attachments, evidence | yes |
| `cortex-es-data` | cortex-es | Cortex search index | yes |
| `cortex-data` | cortex | Cortex job results | yes |
| `shuffle-data` | shuffle-backend | workflows, runs | yes |
| `misp-data` | misp | MISP events | yes |
| `scenarios/` (bind) | scenario-runner | scenario YAMLs | bind from repo |

A `make reset` target nukes all named volumes for a clean start. This is the most-used command during scenario development.

## 7. Host-port bindings

Only the student-facing UIs are bound to the host. Everything else is internal-only.

| Service | Host bind | Purpose |
|---|---|---|
| Portal | `127.0.0.1:8000` | Landing page + live tool status |
| Wazuh dashboard | `127.0.0.1:8443` | SIEM UI |
| DFIR-IRIS | `127.0.0.1:9000` | Case mgmt UI |
| Cortex | `127.0.0.1:9001` | Analyzer UI |
| Shuffle | `127.0.0.1:3001` | SOAR UI |
| MISP | `127.0.0.1:8080` | Threat intel UI |

All bound to loopback only. Documented in the README.

The portal at `127.0.0.1:8000` is the recommended entry point. It reverse-proxies `/api/health/<tool>` over `wachturm-mgmt` to each tool's container, which dodges browser CORS issues and gives the student one URL to bookmark. Tools in profiles that aren't running show as "Not deployed" rather than errors.

## 8. Resource floor and ceiling

- **Floor:** 8 GB RAM, 4 CPU, 40 GB disk — runs the `core` profile (Wazuh + victims + attacker + noise + suricata + portal). Tight; close other apps. A low-RAM tuning note (Phase 1) covers constrained machines.
- **Recommended:** 16 GB RAM, 8 CPU, 40 GB disk — comfortable for `core`; required for `casemgmt`/`soar`.
- **Comfortable:** 32 GB RAM — the full profile with headroom. The OpenSearch/Elasticsearch indexers (Wazuh indexer, Cortex ES) are the main memory consumers.

A `make doctor` target checks the host's resources and warns before `make up`.

## 9. Out of scope for this doc

- Scenario authoring (see `SCENARIO_SCHEMA.md`).
- Build order and phase definitions (see `BUILD_ORDER.md`).
- Claude Code conventions (see `AGENTS.md`).
