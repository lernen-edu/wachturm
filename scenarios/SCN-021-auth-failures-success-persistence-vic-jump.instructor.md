# SCN-021 — Instructor Companion

## Scenario summary

A three-stage intrusion on `vic-jump`: a tight cluster of failed-auth attempts against `mwong`, a success from the same source immediately after, then post-auth persistence via **both** an SSH `authorized_keys` entry **and** a cron job. Correct verdict: **true positive** — account compromise with established persistence. The advanced skill is **building the failures-then-success correlation yourself** from the 5760 cluster and the 5715 success (the platform's 40112 auto-correlation may or may not fire — depending on it is the failure mode), and catching *both* persistence mechanisms. Delivered as a night-shift handoff that was triaged incompletely.

## Learning objectives

- Correlate multiple alert types across a time window into one incident (vs. triaging the loud first stage in isolation).
- Build the "failures-then-success" picture yourself from the 5760 cluster + the 5715 success — and understand that platform auto-correlation (40112) is a *bonus*, not something to wait for (real compromises often don't trip it).
- Hunt for *more than one* persistence mechanism — credential reset alone evicts neither.
- Resist the night-shift framing ("noise, monitoring") — incomplete prior triage is a trap, not a conclusion.

## Required prior knowledge

- SCN-001 (brute→success→recon) and SCN-011 (clean login + persistence) — this builds on both.
- SSH `authorized_keys` and cron as persistence mechanisms.
- That correlated low-severity events can sum to a high-severity incident.

## Estimated timing

- **Student work:** 30–45 minutes
- **Class debrief:** 20 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Reject the handoff's conclusion, keep its facts.** Night shift called the failures "noise, monitoring." That is the error to *catch*, not inherit. Build the timeline yourself.

2. **Stage 1 — the pressure.** A tight cluster of 5760 "authentication failed" for `mwong` from `10.50.10.250`. On its own: looks like the brute/monitoring noise night shift dismissed.

3. **Stage 2 — the transition (you build it).** The failures stop and a success (5715) follows from the *same source*. The pivot is recognizing that **failure-cluster-immediately-followed-by-success from one source = compromise** — *the analyst draws that line on the timeline*. Wazuh's 40112 "multiple authentication failures followed by a success" correlation **may** also fire and confirm it; treat that as a bonus, not the trigger. The Tier-1 failure mode this scenario teaches against is waiting for the platform to label the compromise — many real ones never trip the correlation rule.

4. **Stage 3 — persistence (the part that's easy to miss).** Pivot into the post-auth session: the attacker appended an SSH key to `~/.ssh/authorized_keys` **and** installed a cron job (`*/10 * * * * curl … | sh`). A student who finds one and stops has under-scoped the incident.

5. **Open the IRIS case.** Observables: source `10.50.10.250`, host `vic-jump`, user `mwong` (compromised). Confirm/add.

6. **Set the verdict.**
   - Verdict: `true positive` — credential compromise with established persistence.
   - Severity: `high` — active compromise + persistence.
   - Confidence: `high` — the failure-cluster→success pattern plus two concrete persistence artifacts are unambiguous.
   - Summary: the three-stage chain, *both* persistence mechanisms named, what remediation must cover.

7. **Next steps.** Contain `vic-jump`, reset `mwong`, **remove the SSH key AND the cron job**, escalate to Tier 2 to scope dwell time and any lateral movement.

## Common student errors

1. **Inherits the night-shift verdict ("noise").** Triages only stage 1, closes FP/benign.
   *Redirect:* "Night shift saw the failures and left. What happened *after* they left? Build the timeline past where they stopped looking."

2. **Catches the compromise, misses persistence entirely.** Calls it TP on the failure-cluster→success but recommends only "reset password."
   *Redirect:* "If you reset mwong's password right now, can the attacker still get back in? Look at everything the session wrote to disk."

   *(Watch also for the inverse: a student who only flagged it because Wazuh's 40112 happened to fire — ask them to show you the 5760 cluster and the 5715 and explain the timeline without leaning on the correlation rule.)*

3. **Finds ONE persistence mechanism, stops.** Sees the SSH key, misses the cron (or vice-versa).
   *Redirect:* "You found one way back in. Is that the only thing the session changed? Check scheduled tasks too."

4. **Treats the three stages as three separate tickets.** Doesn't correlate; under-rates each in isolation.
   *Redirect:* "Are these three unrelated events, or one story? What connects them — same what, same when?"

5. **Severity medium ("they only logged in").** Undervalues dual persistence + confirmed access.
   *Redirect:* "Active access plus two independent backdoors — is the incident contained by anything you've done yet?"

## Discussion questions

1. SCN-001, SCN-011, SCN-021 are all SSH-compromise TPs. What does *each* add, and why is SCN-021 the advanced one?
2. Night shift dismissed stage 1. What process or detection would have flagged the stage-2 transition automatically?
3. Two persistence mechanisms were planted. Why would an attacker use more than one, and what does that imply for remediation verification?
4. The brute pressure was slow (every few seconds), not a fast hydra. Why might an attacker pace it that way, and what does that defeat?
5. What's the minimum set of actions that *actually* evicts this attacker, and how do you verify each?

## Stretch challenges

- Write the Wazuh correlation/FIM that would alert specifically on `authorized_keys` or crontab modification post-compromise, and discuss its fleet-wide FP cost.
- Build the Tier-2 escalation timeline artifact (stage, time, evidence, action) a responder could act on directly.

## Auto-grading rubric (from `SCN-021-auth-failures-success-persistence-vic-jump.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `high` (±1 step → `medium`/`critical` credited) | 15 |
| Confidence = `high` (±1 step credited) | 5 |
| Required observables present (source IP, vic-jump, mwong) | 15 |
| Summary contains credential-pressure and persistence/multi-stage keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they build a timeline and correlate, or triage stage 1 only?** This is the entire advanced skill and the night-shift framing is the deliberate trap.
- **Did they catch BOTH persistence mechanisms?** The single highest-signal discriminator. "Found the key, missed the cron" is a realistic, dangerous miss — name it.
- **Remediation completeness.** A correct verdict with "reset the password" is an incomplete, real-world-failing response. Look for "remove key AND cron, then verify."
- **Did they resist the handoff?** Strong students explicitly note night shift mis-triaged stage 1 and say why.
- **Did they correlate independently of the platform?** The strongest tell of Tier-1 readiness here: the student articulates the failures→success→persistence story from the raw 5760/5715 events on the timeline, *without* relying on whether Wazuh's 40112 correlation fired. (Instructor note: SIEM frequency/timeframe correlation rules like 40112 are non-deterministic across runs and are detection *coverage*, not a guarantee — which is exactly why the scenario asserts the deterministic primitives and trains the analyst to build the correlation, not wait for it.)

## MITRE ATT&CK mapping

- **T1110 — Brute Force.** The sustained credential-pressure stage (the MFA-fatigue/repeated-attempt analog, Linux-shaped).
- **T1078 — Valid Accounts.** Post-success operation with valid (now-compromised) credentials.
- **T1098.004 — Account Manipulation: SSH Authorized Keys.** Persistence mechanism #1.
- **T1053.003 — Scheduled Task/Job: Cron.** Persistence mechanism #2.

## Real-world parallel

This is the shape of a great many real intrusions: noisy-then-quiet credential abuse that a tired or rushed first look writes off, a success that the correlation engine *did* flag if anyone connected it, and post-access persistence planted in more than one place so a naive "reset the password" doesn't evict the actor. It is deliberately framed as a botched handoff because that is how these are missed in practice. As v1.0's advanced layered scenario it tests the capabilities that distinguish a Tier-1 who can grow into IR: timeline correlation across event types, skepticism of inherited triage, and remediation that is *complete*, not just *correct*.
