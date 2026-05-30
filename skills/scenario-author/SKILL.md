---
name: scenario-author
description: Author new Wachturm SOC simulator scenarios end-to-end. Use this skill whenever the user wants to create, draft, design, expand, or review a Wachturm scenario; whenever a new scenario is being added to scenarios/; or whenever the user mentions writing a SOC simulation, adding to the scenario library, or producing a beginner/medium/advanced exercise. Triggers also include phrases like "add a scenario," "new scenario," "design an exercise," "build me an FP scenario," or "we need more brute force/phishing/lateral movement coverage."
---

# Wachturm Scenario Author

This skill walks you through producing a complete, mergeable Wachturm scenario — all three required files — in under an hour.

## Read these first

Before writing anything, read:

1. **`SCENARIO_SCHEMA.md`** — the locked YAML spec and the brief/instructor formats.
2. **`scenarios/_taxonomy.md`** — the planned scenario catalog. Check what's already covered and what gaps you'd be filling. Don't author duplicates.
3. **At least one existing scenario trio** if any exist, to internalize the voice and structure.

If you skip these, you'll produce a scenario that fails the merge checklist.

## What you are producing

Every scenario is a trio of three files in `scenarios/`:

```
scenarios/SCN-NNN-<kebab-slug>.yml          ← runner spec (machine-readable)
scenarios/SCN-NNN-<kebab-slug>.brief.md     ← student-facing ticket
scenarios/SCN-NNN-<kebab-slug>.instructor.md ← teacher-facing solution + assessment
```

A scenario without all three files is not mergeable. CI enforces this.

## The authoring workflow

Follow these steps in order. Skipping steps creates rework.

### Step 1 — Pick the gap

Open `scenarios/_taxonomy.md`. Identify a row that's marked "PLANNED" or "OPEN." Confirm:

- The slot is unfilled.
- The slot's category, difficulty, and verdict type fit what you're about to write.
- The next SCN-NNN ID is the lowest unused.

If you're writing something not in the taxonomy, **stop** and propose adding it to the taxonomy first. The taxonomy is the contract; ad-hoc scenarios fragment the library.

### Step 2 — Decide the real-world parallel

Wachturm scenarios must replicate situations a corporate Tier 1 SOC analyst would actually encounter. Before writing, answer in one sentence:

> "This scenario simulates [specific incident type], like when [real-world parallel]."

Examples:
- "Simulates an external SSH brute force attempt that succeeds, like when an exposed jumpbox is found via Shodan."
- "Simulates an authorized vulnerability scanner triggering noisy alerts, like the weekly Nessus run hitting the DMZ."
- "Simulates lateral movement using stolen credentials from workstation to file server, like the post-phishing pivot in countless BEC incidents."

If you can't articulate the real-world parallel, your scenario is contrived and should not be written.

### Step 3 — Calibrate difficulty honestly

| Tier | What the analyst must do | Signal that fits |
|---|---|---|
| **Beginner** | Look at one data source, see one rule fire, reach the verdict from the obvious evidence. | A single Wazuh alert with a clear signature. Verdict obvious within 5–10 minutes. |
| **Medium** | Pivot between two or more data sources, weigh competing interpretations, make a judgment call. | Alert + need to check raw logs, or alert + observable enrichment, or two alerts that need to be correlated. Verdict requires thought. |
| **Advanced** | Correlate 3+ data points across time and/or hosts, navigate ambiguity, possibly distinguish layered TPs from layered FPs. | Multi-stage attack chains, low-and-slow patterns, attacks blended with benign noise, multi-host pivot. Verdict may be defensibly more than one thing. |

Do not mislabel difficulty to make a tier look fuller. A mislabeled beginner scenario will frustrate students; a mislabeled advanced one will bore them.

### Step 4 — Decide the verdict type, and respect distribution

Verdicts:
- **True positive (TP)** — there is an active threat, escalation warranted.
- **False positive (FP)** — alert fired on legitimate activity that triggered detection rules.
- **Benign / benign-suspicious** — activity is unusual or worth checking, but not malicious and not an FP in the rule-fired sense.

Real Tier 1 ticket queues are ~70% FP, ~25% benign-suspicious, ~5% TP. Wachturm leans TP-heavier because TPs teach more, but the library should still feel realistic. Before adding another TP, check the current ratio in `_taxonomy.md` and consider whether an FP or benign scenario would balance the library better.

### Step 5 — Write the YAML spec

Start from `scenarios/_template.yml`. Fill in:

1. **Metadata block** — id, name, description, author, created, difficulty, category, expected_verdict, MITRE techniques (only if TP), duration_minutes.
2. **Setup block** (optional) — one-time pre-conditions like creating users, planting files. Must be idempotent.
3. **Steps block** — the actions the runner executes. Use `delay_seconds` to space events realistically. Real attackers don't run nmap, then hydra, then ssh in the same second.
4. **Expected alerts** — what Wazuh should produce when the scenario runs cleanly. This is for lab integrity checking, not student grading.
5. **Expected observables** — IoCs that should appear in IRIS cases.
6. **Hints** — 2–4 progressive hints. First hint nudges, last hint hands them the answer.
7. **Answer key** — what the student should conclude. Be precise about verdict, severity, confidence, required observables, summary keywords, next steps, and reasoning.

Validate before moving on: `wachturm scenario validate scenarios/SCN-NNN-*.yml`. Fix any schema errors before writing the brief.

### Step 6 — Write the student brief (`.brief.md`)

The brief is what the student sees when they pick up the scenario. It must read like a real SOC ticket, not a textbook problem.

Pick a framing that fits the scenario:

- **SIEM auto-ticket** for technical alerts: "Alert ID #2024-1138 triggered at 03:14:22 UTC. Source: Wazuh rule 5712 — Multiple authentication failures."
- **User-reported** for scenarios that originate from a person: "Helpdesk escalation: user Sarah K reports unable to access shared drive this morning. She mentions getting an 'unusual login' email yesterday."
- **Internal handoff** for handoff drills: "Night shift handoff — this one came in at 02:00, I triaged the initial alert but the activity continued and I need you to pick it up."
- **Threat-intel-driven** for hunt scenarios: "Threat intel feed reports active campaign targeting healthcare sector using technique XYZ. Hunt for IoCs."

Required sections per `SCENARIO_SCHEMA.md` §11. Keep the brief to one screenful — real tickets are brief.

**The brief never contains the answer.** Spoilers belong in the instructor doc.

### Step 7 — Write the instructor companion (`.instructor.md`)

This is where the teaching value lives. The instructor doc has all the spoilers, the pedagogy, and the assessment guidance.

Use the format in `SCENARIO_SCHEMA.md` §12. Required sections:

1. **Scenario summary** (1–2 sentences)
2. **Learning objectives** (concrete, specific skills)
3. **Required prior knowledge**
4. **Estimated timing** (student work + class debrief)
5. **Full solution walkthrough** — step by step what a competent analyst should do
6. **Common student errors** — 3–5 patterns of how students get it wrong, with redirect guidance. This section is gold for instructors.
7. **Discussion questions** — 3–5 questions to provoke class discussion beyond the immediate verdict
8. **Stretch challenges** — optional extensions for fast finishers
9. **Auto-grading rubric** — the YAML's scoring breakdown, written out
10. **Manual assessment guidance** — what the auto-scorer can't measure
11. **MITRE ATT&CK mapping** — technique IDs with one-sentence contextual explanation
12. **Real-world parallel** — a public incident or technique writeup that resembles this scenario

The "common student errors" section is the highest-value part. If you can't list at least three specific ways a student is likely to get this wrong, you don't understand the scenario well enough to teach it. Stop and reconsider.

### Step 8 — Test end-to-end in the lab

```bash
make up
make scenario SCN=NNN
# wait for steps to complete
# manually triage in IRIS as if you were a student
# close the case with what you believe is the correct answer
make score SCN=NNN
```

The score should reflect what you intended. If your "correct" close gets a 75/100, your answer key is misaligned with your scoring rubric — fix one or the other.

Then verify the lab integrity check passes:

```bash
make scenario-verify SCN=NNN
# checks that all expected_alerts fired within their timeframes
```

If any expected alert didn't fire, either your scenario isn't triggering what you thought, or your expected_alerts list is wrong.

### Step 9 — Cross-check the library

Before opening a PR:

- Re-check `_taxonomy.md` — is the category/verdict/difficulty distribution still balanced?
- Does this scenario duplicate another?
- Did you accidentally write your fifth TP in a row? If so, write an FP next.

## Anti-patterns to avoid

These are the patterns that make scenarios bad. If you catch yourself doing any of these, stop and revise.

1. **CTF-flag thinking.** Real SOC tickets don't have "flags." Scenarios should evaluate analytical decisions, not whether the student found a hidden string.
2. **Single-tool tunnel.** A medium or advanced scenario that can be fully solved by staring at one Wazuh dashboard view isn't medium or advanced. Force the pivot.
3. **TP saturation.** If every scenario ends with "yep, attacker, escalate," students learn that the answer is always escalate. Real SOC work is mostly "close, not malicious." Add FPs.
4. **Implausible attack patterns.** No real attacker runs nmap on 1000 ports inside the same second they ssh in. Use `delay_seconds` realistically.
5. **Trick questions.** Wachturm is a learning tool, not a CTF. If your scenario's "correct" answer depends on a obscure technicality the student couldn't reasonably know, you've written a bad scenario.
6. **Ambiguous answers without acknowledging it.** If an advanced scenario could defensibly be triaged as TP-medium or TP-high, your instructor doc must say so and explain how you'd accept both.
7. **Generic briefs.** "Investigate this alert" is not a brief. The brief should feel like a specific moment in a specific organization.

## When you're done

You should have:

- [ ] Three files in `scenarios/`: `.yml`, `.brief.md`, `.instructor.md`
- [ ] `wachturm scenario validate` passes
- [ ] `make scenario SCN=NNN` runs without errors
- [ ] Expected alerts fire in the lab
- [ ] A manual play-through hits the score you intended
- [ ] `_taxonomy.md` updated to mark the slot as filled

If all checkboxes are true, you're ready to PR.

## Template references

The canonical templates live at:
- `scenarios/_template.yml`
- `scenarios/_template.brief.md`
- `scenarios/_template.instructor.md`

Copy these, don't hand-write from scratch.
