# Instructor Guide

This guide is for the educator using Wachturm in a classroom, certification cohort, or self-directed group. It explains the assessment philosophy, how to integrate Wachturm with your syllabus, how to use the per-scenario instructor companion docs, and the practical mechanics of running sessions.

---

## What Wachturm is, from your perspective

Wachturm is a live SOC simulator with three things working together:

1. **A real open-source security stack** running in Docker — students use Wazuh, DFIR-IRIS, Cortex, Suricata, and (in v1.1+) Shuffle and MISP through their actual native UIs. This is not a simulator that mimics what these tools look like. Students learn the workflow on the real software.
2. **A scenario library** of realistic ticket-shaped exercises spanning beginner, medium, and advanced difficulty. Each scenario is graded automatically against an answer key, and each ships with this instructor companion document for deeper assessment.
3. **A scripted activity engine** that produces benign background noise, false positives, and true positives — so the student's queue feels populated, not contrived.

You provide what the tools cannot: pedagogical judgment, discussion facilitation, and assessment of the things an auto-scorer can't measure (clarity of writing, soundness of investigation approach, professional communication).

---

## Assessment philosophy

Wachturm separates assessment into two layers.

**Auto-grading** measures structured correctness: did the student reach the right verdict, set the right severity, attach the right observables, perform appropriate enrichment, take appropriate next steps. The auto-grader runs against the YAML answer key and produces a numerical score with reasoning. This handles the "is the answer right" question and frees you from grading 30 cases by hand.

**Manual assessment** measures judgment, communication, and approach. Each scenario's `.instructor.md` includes a "Manual assessment guidance" section listing the specific things the auto-scorer can't catch: writing quality, investigation methodology, instincts about lateral movement, professional tone. This is the part of the assessment where you contribute the educator's eye.

The numerical auto-score is not the grade. A student can score 95/100 from the auto-grader while writing an unclear summary that wouldn't survive in a real ticket queue; that gap is what you assess in the manual layer.

---

## Suggested syllabus mappings

Wachturm fits into several common curriculum tracks. Below are suggestions, not prescriptions.

### Introduction to SOC operations (single semester)

- Weeks 1–3: Lab setup, dashboard familiarization, first-shift walkthrough (SCN-001 with full instructor support).
- Weeks 4–7: Beginner scenarios. Two scenarios per week, in-class triage, weekly debrief. Focus on building the triage habit.
- Weeks 8–11: Medium scenarios. One scenario per week with class debrief. Focus on pivoting and judgment.
- Weeks 12–13: Advanced scenarios. Slow down — these may take a full session each. Focus on correlation and the "what would change if" hypotheticals.
- Week 14: Practical exam: an unseen scenario the student must triage cold. Use the manual assessment rubric for primary grading.

### Cybersecurity Analyst (CySA+ / equivalent cert prep)

Map scenarios to domains. The CySA+ domain "Security Operations" aligns roughly to Wachturm's beginner and medium tiers. Use Wachturm to make the abstract objective domains concrete.

### Capstone / portfolio

Have each student author **one new scenario** as a capstone deliverable, using `skills/scenario-author/SKILL.md`. Authoring a scenario requires understanding the attack, the detection, the analyst workflow, and the teaching dimension simultaneously — it is the single highest-leverage assessment available.

---

## Running a session

A typical 90-minute classroom session:

| Time | Activity |
|---|---|
| 0:00–0:10 | Brief: distribute the scenario brief (`.brief.md`). Students read individually. |
| 0:10–0:50 | Independent triage. Students work in the lab. Walk around, answer process questions but not "is this the right answer." |
| 0:50–1:00 | Auto-grade. Students run `make score`. |
| 1:00–1:30 | Debrief, discussion. Use the discussion questions from the instructor doc. Address common errors from the instructor doc. |

For advanced scenarios, plan for two sessions: one for triage, one for debrief.

---

## Phase 2: case management & scoring — operational notes

Phase 2 adds the full triage loop (Wazuh alert → auto-created IRIS case → enrichment → scored closure). A few mechanics you must know to facilitate:

- **Bring the lab up with `make up-casemgmt`, not `make up`.** Phase-2 scenarios need DFIR-IRIS and Cortex; `make up` (core profile) is Wazuh-only and the scoring loop will not work. `make up-casemgmt` also bootstraps the IRIS and Cortex API tokens and prints nothing secret to the class.
- **Credentials and URLs: `make first-run-creds`.** It now prints IRIS (`https://127.0.0.1:9000`, `administrator` / the `IRIS_ADM_PASSWORD`) and Cortex (`http://127.0.0.1:9001`, analyst `wachturm-svc` / `wachturm-analyst`). These are sealed-lab defaults; the stack is loopback-only.
- **How a student records a verdict.** IRIS has no native verdict field, so Wachturm uses a **case tag convention**: students tag the case `verdict:<true_positive|false_positive|benign>`, `severity:<low|medium|high|critical>`, `confidence:<low|medium|high>` (case-insensitive). Severity/confidence are graded within ±1 step; verdict is exact and worth 50%. The student's written assessment goes in the case **Summary**, which the scorer reads for the answer key's keyword groups.
- **Enrichment is a deliberate pivot, not an in-IRIS button.** DFIR-IRIS ships no Cortex module; students open Cortex directly, run `ValidateObservable` / `DShield_lookup` (keyless; `AbuseIPDB` only if the operator set a key), and write the finding back into the IRIS Summary. "Never opened Cortex" remains a tool-tunneling pattern to address in debrief.
- **`make score` grades the most recently *closed* case.** A scenario can spawn several cases (one per alert burst). The predictable student error is closing an ambient noise case instead of the one they triaged; the score output names the graded case id, which makes this easy to catch in debrief.
- **The rubric is fixed and transparent** (SCENARIO_SCHEMA.md §6): verdict 50 / severity 15 / confidence 5 / observables 15 / summary 10 / enrichment 5, overridable per scenario via `scoring_weights`. Enrichment is "asked but not graded" for the shipped scenarios — the loop is taught, the points aren't punitive.

## Phase 3a: the v1.0 library, hints, and the tutor — operational notes

- **15 scenarios, no-spoiler names.** Every scenario title describes the *alert and asset* like a real SOC ticket — it never reveals TP/FP/benign. The verdict and discriminator live only in the `.instructor.md` (and the author-only Notes column of `scenarios/_taxonomy.md`); the student-facing `.brief.md` never contains the answer. Do not paraphrase a scenario's verdict from its name in front of the class — the discovery is the exercise. CI enforces this.
- **Verdict mix is deliberate** — 7 TP / 5 FP / 3 BN, 8 easy / 5 medium / 2 hard. The FP/benign half is the point: students must learn that "close, not malicious — verify and document" is most of the job. Several scenarios are deliberate pairs (e.g., SCN-011 TP ↔ SCN-034/SCN-012 BN; SCN-007 TP ↔ SCN-017/SCN-008 FP; SCN-021 cron TP ↔ SCN-015 cron FP): the *same alert shape*, opposite verdicts, decided by context the student must verify. Running a pair back-to-back is high-value.
- **`make hint` costs points and the scorer knows.** Each revealed hint is −5 from the auto-score, and the count is shared with `make score` (a file under `~/.wachturm/hints/`) — a student cannot reveal all hints and still post a perfect score. Hints are progressive (nudge → pointed → near-answer). Use hint usage in debrief as a signal of where a student got stuck, not as a failure.
- **`make tutor` is a coach, not an automation.** It opens a Socratic AI tutor in a *dedicated* terminal; the student does all real work in their own browser/`make` windows. The tutor only ever does read-only state queries to verify the student's claims — it never drives IRIS/Wazuh/Cortex, never runs `make scenario`/`make score` for them, never states the verdict. If a student says "the tutor told me the answer," that is a skill misuse to correct, not expected behavior.
- **Some detection sources are lab-simulated, by design.** The sealed lab has no internet egress and a bridge-sidecar NIDS can't capture peer traffic, so network/Windows/malware-signal scenarios emit the detection event their simulated activity *would* have produced (Suricata EVE, a synthetic AV/cron log line) into the real Wazuh pipeline. The detection→case→triage workflow the student practices is 100% real; only the packet/event *source* is synthetic. If a sharp student notices, that's a good teachable moment about lab fidelity vs. learning objective — not a bug.
- **Build a syllabus with `make scenarios` filters.** `make scenarios FILTER='--difficulty easy --verdict false_positive'` etc. lets you assemble a session set by tier/verdict/category from the 15-scenario library.

## Working with the per-scenario instructor docs

Each scenario has a `.instructor.md` file in `scenarios/`. Before running a scenario in class:

1. **Read the instructor doc in full.** This is non-negotiable. The discussion questions and common-error patterns are how you facilitate; you cannot facilitate from a doc you skimmed in the hallway.
2. **Mentally run the scenario yourself.** Open the brief as a student would. Run `make scenario`. Triage it. Compare your approach to the walkthrough. The walkthrough is one good path, not the only good path — your version may inform how you assess students who took a different route.
3. **Identify which discussion questions fit your cohort.** Not all five questions will land with every group. Pick two or three that match where your students currently are.
4. **Decide your manual assessment focus for this scenario.** Pick one or two items from the manual assessment section to emphasize. Don't try to grade every dimension on every scenario; rotate emphasis across the course.

---

## Honest assessment guidance

Some things to keep in mind as you grade:

- **Tier 1 is about confidence in closing tickets, not about chasing every alert into APT-land.** Praise students who confidently close legitimate FPs quickly. Push back on students who over-escalate every scenario "to be safe" — that's how you burn out a SOC.
- **A wrong verdict with sound reasoning is more valuable than a right verdict with no reasoning.** When auto-grading and manual assessment disagree, your judgment overrides the score.
- **Watch for tool-tunneling.** Some students get stuck in Wazuh and never open IRIS, or never run a Cortex enrichment. Address this in debrief.
- **Watch for AI over-reliance.** Wachturm runs in environments where students may consult AI assistants. The skill `skills/scenario-author/SKILL.md` is designed for AI-assisted authoring; the *triage* of scenarios is a different question. Consider an explicit AI-disclosure policy for scenario triage (suggested template in `docs/ai-policy-template.md` if available, or write your own).

---

## Scaling beyond your cohort

If Wachturm works for your students, consider:

1. **Contributing scenarios.** The taxonomy at `scenarios/_taxonomy.md` lists open slots. The `skills/scenario-author/SKILL.md` walks an author through the process. Scenarios are licensed CC BY-SA 4.0, so contributions stay open.
2. **Contributing instructor docs.** If you teach a scenario and find that the existing instructor doc misses a common error you observed, or you have a better discussion question, PR it. The instructor docs are the most living part of the curriculum.
3. **Reporting outcomes.** Email the maintainers (see README) if Wachturm worked for your students, what you'd improve, and any incidents of "I got my first SOC job" — these are the signals that justify continued investment.

---

## Quick reference — common commands

```bash
make doctor               # check the lab is healthy
make up                   # Phase 1: core profile (Wazuh only)
make up-casemgmt          # Phase 2: core + DFIR-IRIS + Cortex (use this
                          #          for any scenario you intend to score)
make first-run-creds      # print all service URLs + sealed-lab logins
make scenarios            # list the 15-scenario library; filter with
                          #   FILTER='--difficulty hard --verdict benign'
                          #   (--difficulty/--verdict/--category)
make scenario SCN=SCN-001 # run a specific scenario
make score SCN=SCN-001    # auto-grade the most recently closed case
make hint SCN=SCN-001     # reveal the next hint (costs the student 5
                          #   auto-score points; shared with the scorer)
make tutor                # open the Socratic tutor in a new terminal;
                          #   detects installed agents (Claude Code, Codex,
                          #   Gemini CLI, OpenCode, Pi) and lets the student
                          #   pick when several exist (override AGENT=codex)
make reset                # full clean reset between sessions
```

For your own walkthrough, open `http://localhost:8000` (the Wachturm portal) and use it as the entry point.
