# Scenario Taxonomy

This is the planning catalog for the Wachturm scenario library. Each row represents a planned scenario. Authors pick from this list when adding new scenarios; novel scenarios should be added here *before* being authored.

> **Naming rule (2026-05-17):** the `Title` column and every scenario's
> student-facing `name`/brief title describe the **alert and asset** as a
> real SOC ticket would — they never reveal whether the answer is TP, FP,
> or benign. The student discovers the verdict by investigating. The
> author-facing **Notes** column intentionally keeps spoilers (the verdict
> and discriminator) — authors need them; students never read this file.

> **v1.0↔v1.1 boundary rebalanced 2026-05-17 (Fork-1 = B):** the v1.0 set
> is locked to the realistic distribution below (7 TP / 5 FP / 3 BN).
> SCN-005, SCN-014, SCN-020 were **deferred to v1.1** (each depends on a
> lab path that is infra-disproportionate for v1.0 — Linux execve logging
> / vic-web FIM+upload pivot). SCN-012 and SCN-034 were **promoted into
> v1.0** to reach 3 benign scenarios. Cumulative v1.1/v1.2 targets in the
> table below are unchanged planning aspirations.

Status legend:
- ⬜ **OPEN** — slot defined, not yet authored
- 🟡 **DRAFT** — work in progress
- ✅ **DONE** — three artifacts merged and passing CI

Verdict types: `TP` = true positive, `FP` = false positive, `BN` = benign (or benign-suspicious)

## Target distribution at each release

| Release | Total | Beginner | Medium | Advanced | TP | FP | BN |
|---|---|---|---|---|---|---|---|
| v1.0  | 15 | 8 | 5 | 2  | 7 | 5 | 3 |
| v1.1  | 23 | 9 | 8 | 6  | 11 | 8 | 4 |
| v1.2+ | 30 | 10 | 11 | 9 | 14 | 11 | 5 |

This still tilts more TP-heavy than a real SOC ticket queue (~5% TP in production), but TPs are where most pedagogical value lives. The library should *feel* like the FP/benign half is a meaningful portion of the work.

---

## v1.0 library (15 scenarios) — LOCKED

8 beginner / 5 medium / 2 advanced · 7 TP / 5 FP / 3 BN.

### Identity & Access (5 scenarios)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-001 | SSH brute-force alert — vic-jump | Beginner | TP | ✅ | Attacker 10.50.10.250 brute-forces vic-jump admin, succeeds on weak password; Wazuh 5760/5763/40112. **Verdict TP.** |
| SCN-002 | Recurring SSH brute-force alert — vic-jump | Beginner | FP | ✅ | Documented weekly VA scan from 10.50.10.250 vs vic-jump `admin`; 5760/5763 fire, NO 40112 (no success) — the FP discriminator. **Verdict FP.** Slug `ssh-bruteforce-recurring`. |
| SCN-003 | SSH authentication failures then success — bobsmith / vic-jump | Beginner | BN | ✅ | `bobsmith` mistypes 6× then succeeds from 10.50.10.250 vs vic-jump; 5760+5715, NO 5763/40112 — the benign SCN-001 foil. Scenario-owned account (NOT noise-gen's `analyst`). **Verdict BN.** Slug `ssh-auth-failures-bobsmith`. |
| SCN-011 | Login from an unrecognized source then account and file changes — vic-jump | Medium | TP | ✅ | Account takeover: clean SSH success (5715) from an unrecognized source → recon + sensitive-file read + planted authorized_keys (persistence). No 5760/5763/40112 — verdict from source+behaviour, not volume. TP counterpart to SCN-034 (same 5715, opposite verdict). Proven Linux auth path. **Verdict TP.** |
| SCN-012 | Successful login from an unrecognized geographic source — vic-jump | Medium | BN | ✅ | SSH success for a known user from a flagged "foreign" IP; helpdesk/travel record confirms the user is travelling → verify-and-close. Linux auth path (5715) + foreign-IP observable. **Verdict BN.** *(promoted from v1.1)* |

### Endpoint & Malware (1 scenario)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-004 | Known-malware signature detected on vic-work | Beginner | TP | ✅ | EICAR test file lands on vic-work (internal HTTP from a victim host; EICAR-only, no real malware). Low-severity TP — student should still escalate, not dismiss. **Verdict TP.** |

### Network & Lateral Movement (3 scenarios)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-007 | Outbound connection to a threat-flagged IP — vic-work | Beginner | TP | ✅ | Simulated outbound to a "TOR exit node" IP (internal:true — the IP is an observable value, not real egress). Single Suricata alert; verdict obvious once IP enriched. **Verdict TP.** |
| SCN-008 | Internal port scan across the victim subnet | Beginner | FP | ✅ | A documented monitoring host (role assigned to an existing victim, not new infra) runs a Zabbix-style scan. **Verdict FP.** |
| SCN-017 | Periodic outbound beaconing pattern — vic-work | Medium | FP | ✅ | Looks like C2; turns out a cloud-agent heartbeat to a documented-allowlisted endpoint. Teaches "looks suspicious" vs. "is suspicious". **Verdict FP.** |

### Web Application (1 scenario)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-010 | Web-application attack pattern against /login — vic-web | Beginner | TP | ✅ | SQLi attempt wave; automated scanner pattern; Wazuh web-accesslog 31103 + 31152 (real ids). Sustained ~120s wave (robust vs fresh-lab logcollector tail-start). **Verdict TP.** |

### Insider / Admin Behavior (3 scenarios)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-006 | Off-hours bulk file access by an unfamiliar service account — vic-jump | Beginner | FP | ✅ | Newly-deployed Veeam-style backup tool (svc-backup) scanning/archiving files off-hours; legitimate but unfamiliar → FP, verify-and-close via deployment docs. Proven Linux auth path (5715 + post-auth bulk-file session). FP counterpart to SCN-011. GATE PASS 100/100. **Verdict FP.** |
| SCN-015 | New scheduled-task/cron persistence on vic-web | Medium | FP | ✅ | Persistence-like detection (Wazuh built-in rule 2832, deterministic single-event); turns out a documented CI/CD pipeline change. Synthetic crontab-syslog line into the vic-web-tailed dpkg.log (no custom rule). FP counterpart to SCN-021 Stage 3. GATE PASS 100/100. **Verdict FP.** |
| SCN-034 | Off-hours administrative remote access — vic-jump | Medium | BN | ✅ | Off-hours admin remote-in via a documented break-glass procedure; clean SSH success → Wazuh 5715, NO 5760/5763/40112 (absence + verified change-record = benign). **Verdict BN.** *(promoted from v1.2)* |

### Layered Campaigns (1 scenario)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-021 | Repeated authentication failures, then success and a new persistence artifact — vic-jump | Advanced | TP | ✅ | Multi-stage credential abuse (BEC/MFA-fatigue analog, Linux-shaped per anti-pattern #5 — NOT a faked mailbox rule): deterministic 5760 cluster → distinct 5715 success → dual persistence (authorized_keys + cron). expected_alerts asserts 5760+5715 (deterministic primitives); the flaky 40112 correlation is pedagogy not a CI gate (analyst builds the correlation, not the platform). GATE PASS 100/100. **Verdict TP.** |

### Advanced (1 scenario)

| ID | Title (no-spoiler) | Difficulty | Verdict | Status | Notes (author-only — SPOILERS) |
|---|---|---|---|---|---|
| SCN-023 | Anomalous DNS query volume — vic-work | Advanced | TP | ✅ | Low-and-slow data exfil via DNS (simulated on the victims network). Requires statistical thinking and time-window correlation. The "hard one" of v1.0. **Verdict TP.** |

---

## v1.1 expansion (+8 scenarios → 23 total)

### Identity & Access
- SCN-013 | Service-account login at an unusual hour — scheduled-job migration (Medium, FP)
- SCN-016 | Repeated MFA prompts for a single user, eventually approved (Medium, TP) — MFA fatigue

### Endpoint & Malware
- SCN-005 | Shell pipes a remote script to an interpreter — non-admin user (Beginner, TP) *(deferred from v1.0 — depends on Linux execve logging)*
- SCN-014 | Encoded payload in a process command line (Medium, TP) *(deferred from v1.0 — execve logging + Cortex decode pivot)*
- SCN-018 | Suspicious binary signed by an unfamiliar publisher (Medium, FP) — new vendor onboarded
- SCN-019 | Security-tooling disable attempt followed by binary execution (Advanced, TP)

### Network
- SCN-020 | File-integrity alert in a web upload directory (Medium, TP) *(deferred from v1.0 — vic-web FIM + upload + Suricata pivot)*
- SCN-024 | DNS queries to dynamic-DNS infrastructure (Medium, TP) — actor uses No-IP for C2
- SCN-025 | Large outbound transfer at 4 AM (Medium, FP) — cloud backup window

### Advanced
- SCN-026 | Living-off-the-land: scheduled-task persistence + cred dump + quiet exfil (Advanced, TP)

> Note: SCN-012 moved **out** of v1.1 (promoted to v1.0). The +8 / 23-total
> aspiration is unchanged; the exact v1.1 mix is re-pinned when v1.1 is planned.

---

## v1.2 expansion (+7 scenarios → 30 total)

### Multi-stage and ambiguous
- SCN-027 | Ransomware precursor: mass file access + shadow-copy-deletion attempt (Advanced, TP)
- SCN-028 | Compromised CI/CD pushes config that opens an unauthorized port (Advanced, TP)
- SCN-029 | APT-style low-volume encrypted C2 over 72 hours (Advanced, TP) — the genuinely hard scenario

### Specialty
- SCN-030 | Insider data export at end of employment (Advanced, TP) — requires HR context simulation
- SCN-031 | Supply chain: vendor patch contains telemetry that looks like C2 (Advanced, BN)
- SCN-032 | ICS-flavored: unusual modbus traffic between simulated PLC and engineering workstation (Advanced, TP)

### Filler diversity
- SCN-033 | Patch deployment causing FIM noise across the fleet (Beginner, FP) — round out the FP tier

> Note: SCN-034 moved **out** of v1.2 (promoted to v1.0). The +7 / 30-total
> aspiration is unchanged; the exact v1.2 mix is re-pinned when v1.2 is planned.

---

## Adding scenarios not on this list

Don't. Propose an addition here first by opening a PR that:
1. Adds the row to this taxonomy with full metadata
2. Justifies why it's distinct from existing scenarios
3. Identifies which release it targets

The taxonomy is the planning contract. Ad-hoc scenarios fragment the curriculum and skew the realistic-distribution targets.
