# SCN-015 — Instructor Companion

## Scenario summary

Wazuh's built-in crontab-change rule (2832) fires on `vic-web` for a new scheduled job installed by the `deploy` account. A new cron entry is textbook persistence (T1053.003) — but here it is a documented CI/CD pipeline change. Correct verdict: **false positive**, resolved by verifying the change/pipeline record. The deliberate FP counterpart to SCN-021's Stage-3 cron persistence (same artifact, opposite verdict, decided by the covering record).

## Learning objectives

- Recognize a persistence detection (cron/scheduled-task) and that legitimate automation (CI/CD, config mgmt, backups) creates the same artifacts.
- Use change-management / pipeline records as the deciding evidence.
- Distinguish a false positive (rule fired on sanctioned automation) from benign and from a real persistence TP.
- Hold the SCN-021 contrast: the *same* crontab change is a TP there (post-compromise, no record) and an FP here (documented deploy).

## Required prior knowledge

- What cron / scheduled tasks are and why they're a persistence mechanism (T1053.003).
- That CI/CD and config-management tooling installs scheduled jobs as normal operation.
- False positive vs. benign vs. true positive.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Wazuh rule 2832 "Crontab entry changed" on `vic-web`, account `deploy`. Note the technique: this is persistence-class.

2. **Withhold the verdict.** A new cron job is *suspicious* (persistence) — it is not *malicious* on its own. The same artifact is created by attackers and by every deployment pipeline on earth.

3. **Identify the actor and pivot to change management — the deciding step.** The account is `deploy` (a service/deployment identity). Check CI/CD and change records for `vic-web` at this time: a current pipeline run / change ticket covers this scheduled-job change.

4. **Open the IRIS case.** Observable: host `vic-web` (add the `deploy` account / the job detail if surfaced). Confirm/add.

5. **Set the verdict.**
   - Verdict: `false positive` — rule fired on a documented, sanctioned CI/CD action.
   - Severity: `low`.
   - Confidence: `medium` — rests on the change/pipeline record being authoritative and matching.
   - Summary: crontab change on vic-web by `deploy`, verified against CI/CD change record; FP; recommend tuning/allowlisting the pipeline identity.

6. **Next steps.** Verify/record the CI/CD change, document, close as false positive (optionally: recommend the deployment service account's expected cron changes be allowlisted so this isn't recurring Tier-1 toil).

## Common student errors

1. **"New cron job ⇒ persistence ⇒ TP."** Pattern-matches the technique, skips the actor/record check.
   *Redirect:* "What legitimate, extremely common thing installs cron jobs constantly? How would you tell that apart from an attacker here?"

2. **Doesn't check change management; guesses either way.** Verdict reached without verification is unverified, both directions.
   *Redirect:* "Where would a deployment account's scheduled-job change be recorded? Did you look before deciding?"

3. **Marks benign rather than false positive.** Legitimate automation that *tripped a detection* is an FP; the precision matters for tuning.
   *Redirect:* "Did the rule fire on something that wasn't an attack? What's that called, versus 'benign'?"

4. **Confuses with SCN-021.** SCN-021's Stage 3 plants the *same* kind of cron persistence — but post-compromise, with no covering record. Applying that TP reasoning here (or vice-versa) without checking the record is the error.
   *Redirect:* "SCN-021 had a cron job too. What made it malicious there that's absent here — and did you verify that difference, or assume it?"

5. **Closes FP, recommends no tuning.** Leaves the SOC re-triaging every pipeline deploy forever.
   *Redirect:* "This pipeline deploys on a schedule. What should change so the next analyst doesn't burn 20 minutes on it?"

## Discussion questions

1. SCN-021 (Stage 3) and SCN-015 produce the same crontab-change artifact, opposite verdicts. List every signal that separates them, ranked by decisiveness.
2. An attacker who compromised the `deploy` account would install cron persistence that *looks* exactly like a pipeline change. What additional signal distinguishes that, and is Tier 1 expected to catch it?
3. What's the operational cost of (a) escalating every pipeline cron change vs. (b) blanket-allowlisting the `deploy` account's crontab changes?
4. Where is the FP/benign line? Use SCN-003 (benign) and this scenario (FP) as the two anchors.
5. The detection (rule 2832) is correct and useful. How do you keep its value while not drowning Tier 1 in pipeline noise?

## Stretch challenges

- Write the Wazuh tuning (rule override / allowlist) for `deploy`-account crontab changes on `vic-web`, and reason about the blind spot it creates (compromised-deploy-account case).
- Design a detection that distinguishes a *pipeline* cron change from a *hand-installed* one by the same account (timing vs. a pipeline run, job content, parent process).

## Auto-grading rubric (from `SCN-015-new-cron-persistence-vic-web.yml`)

| Criterion | Points |
|---|---|
| Verdict = `false_positive` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (vic-web) | 15 |
| Summary contains cron/persistence and FP/CI-CD keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they verify the change record, or judge the technique?** The scenario *is* the verification. A correct verdict without checking CI/CD is unverified luck.
- **FP vs. benign precision.** "Rule fired on sanctioned automation" (FP) vs. vague "it's fine" (benign). Drives tuning.
- **The SCN-021 contrast.** Strong students explicitly pair them: same cron artifact, TP there / FP here, decided by the covering record + actor context. That comparison is the learning.
- **Did they recommend tuning?** A closed FP with no follow-up is incomplete for a *recurring pipeline* trigger.

## MITRE ATT&CK mapping

None for the verdict (this is sanctioned CI/CD). For instructor context: the *detection* covers **T1053.003 — Scheduled Task/Job: Cron**; the teaching point is that a correct T1053.003 detection still requires actor/record context to disposition — the technique is present, the adversary is not.

## Real-world parallel

Crontab/scheduled-task change alerts are a high-volume FP source anywhere CI/CD, configuration management (Ansible/Puppet/Chef), backup agents, or package post-install scripts run — they all legitimately install scheduled jobs, tripping the very same (correct, valuable) persistence detections used to catch attackers. Mature SOCs resolve these by actor + change-record correlation and tune the known pipeline identities, accepting the explicit residual risk (a compromised deploy account) as a higher-tier concern. Paired with SCN-021 — where the identical cron artifact is real post-compromise persistence — this teaches the decisive instinct: the covering record and the actor context, not the technique, carry the verdict.
