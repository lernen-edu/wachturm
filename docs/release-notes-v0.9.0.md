# Wachturm v0.9.0 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE.** This is the complete Wachturm
> v1.0 product, published so external evaluators can use it exactly as a
> student would — clone, run, triage, get graded, learn. **It is not yet
> v1.0.0.** The v1.0.0 release is gated on a human-testing milestone
> (independent external testers + an educator review), and **v0.9.0 is the
> artifact those testers evaluate.** When that gate passes, v1.0.0 follows
> as the validated release. Treat v0.9.0 as a release candidate:
> feature-complete and engineering-verified, not yet validated by
> independent learners.

## What Wachturm is

An open-source, Docker-based **Tier-1 SOC analyst simulator**. You run
realistic alerts through a real detection/IR stack — Wazuh (SIEM/HIDS),
Suricata (NIDS), DFIR-IRIS (case management), Cortex (observable
enrichment) — triage them with the four-step method (Read → Investigate →
Decide → Document), and get auto-graded against a scenario answer key. A
Socratic AI tutor coaches without giving answers.

## What's in v0.9.0

- **15 scenarios**, three files each (runner spec + student brief +
  instructor companion), across identity, endpoint, network, web,
  insider, and a layered campaign. Realistic **7 true-positive /
  5 false-positive / 3 benign** verdict mix. No-spoiler titles
  (CI-enforced) — you discover the verdict by investigating.
- **`make up-casemgmt`** brings up the full core + case-management stack;
  **`make scenario`** runs a scenario; **`make score`** grades your closed
  IRIS case (verdict / severity ±1 / confidence ±1 / observables / summary
  keywords / enrichment); **`make hint`** gives progressive hints (−5 pts
  each, shared with the scorer); **`make scenarios`** lists/filters the
  library.
- **`make tutor`** — a Socratic AI tutor in a dedicated terminal. It
  **scans your machine for an installed agent** (Claude Code, Codex,
  Gemini CLI, OpenCode, or Pi) and, if several are present, lets you pick.
  It coaches via read-only state queries, never drives your tools, never
  hands over the answer, and remembers your progress across sessions.
- **Sealed loopback lab** — attacker/victim networks have no egress; only
  loopback UIs are exposed; EICAR-only, no real malware.
- A complete **student curriculum** (`docs/student/`) and an **instructor
  guide** (`docs/instructor-guide.md`).

## Getting started

`cp .env.example .env` → `make up-casemgmt` → `make first-run-creds` →
`make portal`, then follow **`docs/student/README.md`**. Budget ~16 GB RAM
for Docker; the first build is slow. New to SOC work? Start with
`docs/student/02-first-shift.md` — a hand-held first scenario.

## Evaluating this release

Wachturm aims to teach Tier-1 triage **without a human instructor**, so the
most valuable feedback is wherever the docs or the tutor left you stuck.
If you're an invited evaluator, the test procedure and where to send
feedback came with your invitation. Otherwise, please **open an issue on
this repository**: tell us where you got stuck, which scenarios you ran
and your scores, how many hints you needed, and anything the curriculum or
tutor failed to make clear. *"I didn't understand what to do after the
alert fired"* is the single most useful sentence you can write.

## Known limitations (deferred to v1.1+)

- Suricata NIDS scenarios use scenario-driven EVE injection (a Docker
  bridge sidecar can't passively capture inter-container traffic); real
  packet capture comes later.
- Endpoint/Web scenario depth is intentionally thinned to keep the
  realistic verdict mix; restored in v1.1.
- SOAR (Shuffle) and threat-intel (MISP) are wired as roadmap profiles,
  not part of the v1.0 learning loop.
- A freshly-built lab can occasionally fail `LAB_INTEGRITY` on the *first*
  scenario (the agent connects before its log collector attaches); an
  immediate re-run passes.
- The tutor's cross-session memory and multi-agent launch are new in this
  release — engineering-verified and adversarially self-reviewed, but not
  yet proven by repeated real-learner use. That's exactly what this
  evaluation covers.

## Stability hardening

Adversarial self-play and own-context persona testing found and fixed a
Wazuh `analysisd` wide-JSON flood (CIS SCA + Suricata `stats` telemetry)
that could silently drop scenario alerts on a long-running lab, plus a
class of learner-doc and tutor accuracy defects (a wrong profile in the
first-scenario walkthrough, an untaught case-tagging convention that is
70% of the score, and a `make scenario` step-description spoiler leak,
among others).

---

*Engineering-verified; awaiting the independent human-tester + educator
gate before v1.0.0. Licensed Apache-2.0 (code) and CC BY-SA 4.0
(scenarios & documentation).*
