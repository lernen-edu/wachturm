# SCN-NNN-kebab-slug — Instructor Companion

> **Audience:** instructors using Wachturm in a classroom or 1:1 tutoring context. This document never reaches the student.
>
> **Match the voice of:** SCN-001-ssh-brute-force.instructor.md — peer-to-peer, practical, with real classroom observations once you have them. Until you've taught it, the "Common student errors" section will be your best guess; that's fine. Update it after the first cohort runs through.

---

## At a glance

- **Difficulty:** beginner | medium | advanced
- **Estimated student time:** N minutes
- **Verdict:** true_positive | false_positive | benign
- **MITRE techniques:** T#### (if any)
- **Teaches:** 1–2 sentence summary of the pedagogical goal.

## Scenario overview

What is this scenario simulating in the real world? Be specific. Reference real incident patterns, not generic categories. A reader who has done Tier 1 work for 6 months should recognize "yeah, I've seen this in production."

What does the student see when they run `make scenario SCN=NNN-...`? Briefly describe the alert(s) that fire, the time window, the noise level.

## Solution walkthrough

A step-by-step of how a competent Tier 1 analyst should triage this. Use the four-step triage method as your structure:

### Step 1 — Read

What should the student notice in the brief and in Wazuh's alert view? Which fields matter? Which are red herrings or context?

### Step 2 — Investigate

What observables should they extract? Which pivots should they make? What Cortex analyzers (if any) help here? What should they look at in adjacent logs (process events, network flows, sibling alerts)?

### Step 3 — Decide

What is the correct verdict and why? What evidence supports it? What evidence would have supported the opposite verdict, and why does this scenario rule that out?

### Step 4 — Document

What should the case summary contain? What observables should be in the case? What severity should the student set, and why?

## Common student errors

> Fill in after you've taught the scenario at least twice. Until then, this section is your best guess.

- **Verdict-jumping:** description of how students often jump to a verdict without sufficient investigation. What's the tell? How do you redirect?
- **Missed observable:** what's a piece of evidence students often miss? Why? How do you point them toward it without giving it away?
- **Over-confidence:** when do students mark high confidence on a verdict they haven't earned?
- **Under-investigation:** what investigative step do students skip that they shouldn't?

## Discussion questions

3–6 questions for post-scenario debrief. These should:
- Encourage reflection on the *method*, not just the answer.
- Connect to real-world practice ("how would this differ at scale, with 1000 of these per day?").
- Prompt thinking about what would change the verdict ("what additional evidence would have made you change your decision?").

Examples:
1. What was the single most informative observable in this case? Why?
2. If you ran a Cortex analyzer that came back empty, what does that tell you? How would you weight it?
3. The brief said `<X>`. What if it had said `<Y>` instead — would the verdict change? Why?
4. How does this incident pattern map to your real environment (or one you've worked in)? What would be different?

## Solution rubric (auto-grading reference)

Maps to the `answer_key` block in the YAML. The auto-scorer evaluates against the YAML; this section explains the rubric in human terms for instructors who want to grade manually or review a student's auto-graded case.

| Element | Required for full credit | Points |
|--|--|--|
| Correct verdict | <true_positive\|false_positive\|benign> | 30 |
| Confidence appropriate to evidence | At least `medium` with full investigation | 15 |
| Required observables in case | List from YAML's `required_observables` | 20 |
| Required actions performed | List from YAML's `required_actions` (e.g., Cortex analyzer runs) | 15 |
| Case summary mentions key concepts | Free-text contains terms from YAML | 10 |
| Case severity set appropriately | high for TP, low for FP/benign typically | 10 |
| **Total** | | **100** |

Hints deduct 5 points each from the final score.

## Variations and extensions

Optional. Ideas for instructors who want to adapt this scenario:

- Replace `<X>` with `<Y>` to flip the verdict.
- Add `<additional element>` to make it advanced.
- Pair with `<related SCN-NNN>` for a longer exercise.

## Field notes

> Empty until you've taught the scenario. Add observations from real cohorts as you go — what worked, what surprised you, what you'd change next time. These are gold for future instructors (including future-you).
