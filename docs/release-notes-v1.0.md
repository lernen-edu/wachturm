# Wachturm v1.0.0 — Release Notes (DRAFT)

> **Status: UNRELEASED — pending external validation.** Engineering for
> Phase 3a is complete; the `v1.0.0` tag is gated on the external-tester
> and external-educator sign-off in `docs/v1.0-tester-feedback.md`
> (three DoD items a build agent cannot satisfy). Do not tag or announce
> until that section is signed off by real people.

## What Wachturm v1.0 is

An open-source, Docker-based **Tier-1 SOC analyst simulator**. A student
runs realistic alerts through a real detection/IR stack — Wazuh
(SIEM/HIDS), Suricata (NIDS), DFIR-IRIS (case management), Cortex
(observable enrichment) — triages them with the four-step method
(Read → Investigate → Decide → Document), and is auto-graded against a
scenario answer key. A Socratic tutor coaches without giving answers.

## Highlights

- **15 scenarios**, three files each (runner spec + student brief +
  instructor companion), spanning identity, endpoint, network, web,
  insider, and a layered campaign. Realistic verdict mix —
  **7 true-positive / 5 false-positive / 3 benign** — so the library
  *feels* like a real ticket queue, not "always escalate."
- **No-spoiler scenario names.** Titles describe the alert and asset
  like a real SOC ticket; the student discovers TP/FP/benign by
  investigating. CI enforces this and the three-file requirement.
- **`make score`** — structured rubric grading of the student's closed
  IRIS case (verdict / severity±1 / confidence±1 / observables /
  summary keywords / enrichment).
- **`make hint`** — progressive hints that cost 5 points each; the count
  is shared with the scorer so hints can't be farmed for free.
- **`make tutor`** — launches a Socratic AI tutor in a dedicated
  terminal: it scans for an installed agent (Claude Code, Codex, Gemini
  CLI, OpenCode, Pi) and lets the student pick, coaches via read-only
  state queries, never drives the student's tools, and remembers progress
  across sessions.
- **`make scenarios`** — lists/filters the library by difficulty,
  category, and verdict type.
- **Live tutor state** — the portal `/api/state` exposes
  `active_scenario` / `scenario_status` / `hints_used` so the tutor
  always knows where the student actually is.
- **Sealed loopback lab** — attacker/victim networks have no egress
  (hard rule); only loopback UIs are exposed; EICAR-only, no real
  malware.

## Stability hardening (Phase 3a)

Adversarial self-play during Phase 3a found, root-caused, and fixed a
detection-pipeline failure that the per-scenario authoring gate could
not see:

- **Wazuh `analysisd` wide-JSON flood — fixed.** Two background sources
  emitted JSON records wider than analysisd's decoder field cap (CIS
  SCA configuration-assessment results; Suricata `stats` telemetry,
  every 8 s), eventually degrading analysisd so scenario alerts were
  silently dropped. Neither is used by any scenario; both are now
  disabled at the source. The earlier "all scenarios pass" gate was
  real but ran each scenario within ~2 minutes of a fresh lab, before
  the flood built up — so a long-running lab (a real session) could
  hit what the gate never did. Verified fixed by a 4-cycle fresh-lab
  battery (zero decoder errors; scenarios score 100/100; Suricata
  alert path unaffected). Details: `docs/v1.0-tester-feedback.md`.

## Known limitations / deferred to v1.1+

See `docs/v1.1-backlog.md`. Headlines:

- Suricata NIDS scenarios use scenario-driven EVE injection (a Docker
  bridge sidecar cannot passively capture inter-container traffic);
  real packet capture is Phase 5.
- Endpoint/Web scenario depth intentionally thinned in v1.0 to keep the
  realistic verdict mix; restored in v1.1.
- Shuffle (SOAR) and MISP (threat intel) are Phase 4 / v1.1.
- A freshly-built lab can occasionally fail `LAB_INTEGRITY` on the
  *first* scenario (agent connected before its log collector has
  attached); an immediate re-run passes. Low severity, tracked for
  v1.1.

## Upgrade / install

Fresh project — see `README.md` and `docs/student/README.md`.
`make doctor` checks host prerequisites; `make up-casemgmt` brings up
the full Phase-1+2 stack and waits until victim agents are connected.

## Credits

Built with the `scenario-author` skill; scenarios CC BY-SA 4.0. See
`THIRD_PARTY.md` and `LICENSE`.

---

_Fill the exact tag date and the tester/educator sign-off summary from
`docs/v1.0-tester-feedback.md` at release time._
