# Wachturm

> **Stand watch. Triage. Escalate.**
>
> An open-source, Docker-based Tier 1 SOC analyst simulator. Real tools, real alerts, real triage decisions — without a real production network on the line.

> **v0.9.0 — public evaluation preview.** Feature-complete and engineering-verified; **v1.0.0 follows once independent learner testing passes.** See [`docs/release-notes-v0.9.0.md`](docs/release-notes-v0.9.0.md).

---

## What is this?

Wachturm is a self-hosted training environment for aspiring SOC analysts. It runs a real open-source security stack — SIEM/EDR/HIDS, NIDS, case management, and observable enrichment — alongside a scripted attack/benign activity engine and a library of scenarios with answer keys. (SOAR and threat-intel tooling are on the post-v1.0 roadmap; see [Roadmap](#roadmap--not-in-v10).)

You sit in the analyst's chair. You read alerts. You decide: true positive, false positive, or benign? You enrich observables, write your case, and close it. Wachturm grades your work against the answer key.

It is built for college students and self-learners who want to feel what Tier 1 SOC work is actually like before they get hired. It is **not** a production SOC, a vulnerable-VM playground, or a red team tool.

## Stack

Shipping in **v1.0** (the `core` + `casemgmt` profiles):

- **SIEM + EDR + HIDS:** [Wazuh](https://wazuh.com/) 4.9 — GPLv2
- **NIDS:** [Suricata](https://suricata.io/) 8.0 — GPLv2
- **Case management:** [DFIR-IRIS](https://dfir-iris.org/) — LGPL3
- **Observable enrichment:** [Cortex](https://github.com/TheHive-Project/Cortex) — AGPLv3
- **Attack/benign activity:** per-scenario scripted activity (the `atk-kali` container + a benign-noise generator). Techniques are inspired by the [Atomic Red Team](https://atomicredteam.io/) catalogue but expressed directly in scenario YAML — Wachturm does not bundle the ART framework.
- **Orchestration:** Docker Compose v2

### Roadmap — not in v1.0

These are real future stack, wired as Compose profiles but **not part of the v1.0 learning loop yet**:

- **SOAR:** [Shuffle](https://shuffler.io/) — AGPLv3 — *Phase 4 / v1.1*
- **Threat intel:** [MISP](https://www.misp-project.org/) — AGPLv3 — *Phase 4 / v1.1*

See [`docs/release-notes-v1.0.md`](docs/release-notes-v1.0.md) for the full v1.0 scope and known limitations.

> Wachturm originally drafted TheHive 5 as the case management tool. The dependency license audit identified TheHive 5 as no longer open source under any OSI-approved license, so v1 ships with DFIR-IRIS instead. See [`THIRD_PARTY.md`](THIRD_PARTY.md) for the full dependency audit.

## First 10 minutes

From a clean clone to your first triaged alert in the portal:

> **Requires:** Docker 24.x, Docker Compose v2, **16 GB RAM recommended** (the full v1.0 loop — Wazuh + DFIR-IRIS + Cortex — needs ~9.5 GB; 8 GB only fits the Wazuh-only `core` profile), 40 GB disk. The first start builds images and can take several minutes; subsequent starts are quick.

> **Platform:** macOS and Linux run the commands below as-is. **On Windows**, use WSL2 + Docker Desktop and run everything inside the Ubuntu (WSL2) shell — see [`docs/student/windows-setup.md`](docs/student/windows-setup.md).

```bash
git clone https://github.com/lernen-edu/wachturm
cd wachturm
make doctor          # check your system can run this
cp .env.example .env
make up-casemgmt     # the full v1.0 stack: Wazuh + Suricata + DFIR-IRIS + Cortex
make first-run-creds # print the tool URLs + sealed-lab logins
make portal          # opens http://localhost:8000 in your browser
make scenario SCN=SCN-001
```

> **Use `make up-casemgmt`, not `make up`.** `make up` is the Wazuh-only `core` profile (Phase 1) — alerts fire but there is no DFIR-IRIS case to triage and `make score` cannot grade you. Every v1.0 scenario is *read the alert → investigate → open/close the IRIS case → `make score`*, which needs the `casemgmt` profile.

The portal at <http://localhost:8000> is your console — it shows every tool's live status and is your one bookmark. Within ~60 s of `make scenario` you'll see the alert in **Wazuh**; the matching case appears in **DFIR-IRIS**. Triage it, close it, then:

```bash
make score SCN=SCN-001     # grade your closed IRIS case against the answer key
```

For the full guided first-shift walkthrough, read [`docs/student/02-first-shift.md`](docs/student/02-first-shift.md). New to all of this? Start at [`docs/student/README.md`](docs/student/README.md).

## Profiles

Wachturm uses Compose profiles to let you pick what to run:

| Profile | What it adds | RAM | Status |
|---|---|---|---|
| `core` | Wazuh, Suricata, victims, attacker, benign noise | ~6.5 GB | v1.0 |
| `casemgmt` | DFIR-IRIS + Cortex | +3 GB | **v1.0 — required for scoring** |
| `soar` | Shuffle | +1.5 GB | v1.1+ roadmap |
| `intel` | MISP | +2 GB | v1.1+ roadmap |

- `make up-casemgmt` → core + casemgmt — **use this for v1.0** (the full triage + scoring loop)
- `make up` → core only (Phase 1; Wazuh alerts only, no case management or scoring)
- `make up-full` → everything, including the v1.1+ roadmap profiles (not part of the v1.0 curriculum)

## Scenarios

Each scenario is a YAML file in `scenarios/` plus a markdown brief. The runner executes the steps, Wazuh detects, IRIS tracks the case, and `make score` grades your conclusions.

```bash
make scenarios               # list all scenarios
make scenario SCN=SCN-001    # run a specific scenario
make hint SCN=SCN-001        # get a hint (costs points)
make score SCN=SCN-001       # grade your closed case
```

Scenario format is documented in [`SCENARIO_SCHEMA.md`](SCENARIO_SCHEMA.md). Contributions welcome — scenarios are licensed CC BY-SA 4.0.

## Documentation

**For students** — start at **[`docs/student/README.md`](docs/student/README.md)**. The student curriculum teaches you both how to use the environment and how to actually do Tier 1 triage work. Read it in order if you're new.

**For students who want an AI tutor** — run `make tutor` in a separate terminal window. This detects which coding agents you have installed — Claude Code, Codex, Gemini CLI, OpenCode, or Pi — and, if several are present, lets you pick which one to launch with the **[`skills/wachturm-tutor/`](skills/wachturm-tutor/)** skill loaded — a Socratic tutor that coaches you through scenarios without giving you the answers. The tutor lives in its own terminal; you do your actual SOC work in browsers and your other terminals. The tutor can verify your work by querying the running stack directly (read-only), but it won't drive your tools for you. See the skill's `SKILL.md` for details.

**For instructors:**
- [`docs/instructor-guide.md`](docs/instructor-guide.md) — running Wachturm in a classroom, assessment philosophy, syllabus mappings
- [`docs/release-notes-v1.0.md`](docs/release-notes-v1.0.md) — v1.0 scope, stability notes, and known limitations

**For contributors:**
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to contribute, and the public/upstream model
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — how the stack fits together (and the network/safety model)
- [`SCENARIO_SCHEMA.md`](SCENARIO_SCHEMA.md) — the scenario YAML spec
- [`skills/scenario-author/SKILL.md`](skills/scenario-author/SKILL.md) — guided authoring of new scenarios
- [`skills/wachturm-tutor/SKILL.md`](skills/wachturm-tutor/SKILL.md) — the student tutoring skill
- [`SECURITY.md`](SECURITY.md) — reporting security issues
- [`THIRD_PARTY.md`](THIRD_PARTY.md) — dependency license audit

## ⚠ Safety

Wachturm runs *real* attack tooling against *real* services inside isolated Docker networks. The attacker container has no internet egress by default. Do not modify the network model, do not expose ports beyond `127.0.0.1`, and do not run Wachturm on a machine that holds production data without proper segmentation. See [`ARCHITECTURE.md`](ARCHITECTURE.md) §3 for the network model.

## License

- **Code:** [Apache License 2.0](LICENSE) — permissive, with explicit patent grant. Covers the Python runner, Compose configuration, custom Dockerfiles, scoring engine, and infrastructure.
- **Scenarios, briefs, instructor companion docs, and other documentation:** [CC BY-SA 4.0](LICENSE-content) — share-alike, attribution-required. Covers all educational content.
- **Third-party dependencies:** documented in [`THIRD_PARTY.md`](THIRD_PARTY.md) with their respective licenses preserved.

Apache 2.0 was chosen over AGPLv3 to maximize educational adoption. The curriculum itself (scenarios and instructor docs) is protected by CC BY-SA's share-alike clause, which is the right protection for educational content.

## Acknowledgments

Built for college students entering Tier 1 SOC roles. Special thanks to the maintainers of Wazuh, DFIR-IRIS, TheHive (whose Cortex still lives on), Shuffle, MISP, Suricata, and Atomic Red Team — without their work, this project couldn't exist.
