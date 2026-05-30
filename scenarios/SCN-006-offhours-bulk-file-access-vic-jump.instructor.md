# SCN-006 — Instructor Companion

## Scenario summary

An off-hours SSH login to `vic-jump` by the unfamiliar `svc-backup` account, followed by bulk file enumeration and archiving. The behaviour is genuinely ambiguous — identical to exfil prep and to a backup job. Correct verdict: **false positive** — it is a newly-deployed, documented backup tool's sanctioned activity, resolved by verifying the documentation. The deliberate FP counterpart to SCN-011 (same shape, opposite verdict, decided by the actor's verified legitimacy).

## Learning objectives

- Recognize that "bulk file read/archive" is ambiguous and must be resolved by *who/what*, not the behaviour alone.
- Use service-account inventory and change/deployment records as the deciding evidence.
- Distinguish a false positive (rule fired on sanctioned tooling) from a benign and from an exfil TP.
- Hold the SCN-011 contrast: same off-hours-login+session shape, opposite verdict, decided by verified actor legitimacy.

## Required prior knowledge

- SSH auth and the meaning of a Wazuh 5715 success alert.
- What backup tooling does and why it resembles staging/exfil.
- False positive vs. benign vs. true positive; service accounts.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Wazuh 5715 on `vic-jump`, account `svc-backup`, source `10.50.10.250`, 03:12 UTC. No 5760/5763/40112 — clean login, not brute force.

2. **Withhold judgment on the session behaviour.** `find … | head`, `du -sh`, `tar -cf …` over many files = data staging *or* a backup. The behaviour does not decide it.

3. **Identify the actor — the deciding step.** Is `svc-backup` an inventoried service account? Check the service-account inventory and recent change/deployment records. It is the account for a newly-deployed (hence unfamiliar to day shift) backup tool; the timing matches its documented window and the files are within its documented scope.

4. **Open the IRIS case.** Observables: source `10.50.10.250`, host `vic-jump`, user `svc-backup`. Confirm/add.

5. **Set the verdict.**
   - Verdict: `false positive` — rule fired on sanctioned, documented backup tooling.
   - Severity: `low`.
   - Confidence: `medium` — rests on the deployment/inventory documentation being authoritative.
   - Summary: clean off-hours svc-backup login + bulk read/archive; verified as the newly-deployed documented backup tool; FP.

6. **Next steps.** Verify/record the backup tool and its service account in asset/change management, document, close as false positive (optionally: recommend the new service account be added to the analyst-known inventory so this isn't a cold triage next time).

## Common student errors

1. **"Bulk file archive off-hours by an unknown account ⇒ exfiltration TP."** Reasons from the (genuinely scary) behaviour without identifying the actor.
   *Redirect:* "Everything you listed also describes a backup job. What single piece of evidence tells you which this is — and is it in the session, or somewhere else?"

2. **Doesn't check the service-account/deployment records.** Guesses either direction.
   *Redirect:* "Where would a newly-deployed backup tool's service account be documented? Did you look before deciding?"

3. **Marks benign instead of false positive.** Legitimate activity that *tripped the detection* is an FP; the precision matters for tuning and metrics.
   *Redirect:* "Did the rule fire on something that wasn't an attack? What's that called exactly, versus 'benign'?"

4. **Trusts 'it's a service account, probably fine' without verifying.** The mirror error to #1 — waving it through on the name alone is as wrong as escalating on the behaviour alone.
   *Redirect:* "`svc-backup` is just a string an attacker can also name an account. What actually confirms it's the real backup tool?"

5. **Confuses with SCN-011.** Applies SCN-011's TP reasoning (or vice-versa) without noting the deciding difference is the *verified legitimacy of the actor*.
   *Redirect:* "Compare to SCN-011. Same off-hours login + active session. What's different here — and what evidence establishes it?"

## Discussion questions

1. SCN-011 and SCN-006 are nearly the same alert + session shape. Enumerate every signal that separates them, ranked by how decisive each is.
2. An attacker who compromised the real `svc-backup` credentials would look exactly like this. What additional signal would still catch them?
3. What's the operational cost of (a) escalating every backup job vs. (b) blanket-trusting any account named `svc-*`?
4. Where is the FP/benign line? Use SCN-003 (benign) and this scenario (FP) as the anchors.
5. The account was unfamiliar only because the tool was newly deployed. Whose process gap is that, and how do you close it?

## Stretch challenges

- Propose the asset/change-management hook that would let this be auto-enriched ("svc-backup = sanctioned, window 03:00–04:00, scope /srv,/home") and argue why auto-closing it is still risky.
- Design a detection that distinguishes the real backup job from a credential-thief abusing the backup account (scope, timing, destination of the archive).

## Auto-grading rubric (from `SCN-006-offhours-bulk-file-access-vic-jump.yml`)

| Criterion | Points |
|---|---|
| Verdict = `false_positive` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (source IP, vic-jump, svc-backup) | 15 |
| Summary contains backup/service-account and FP/documented keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they resolve it by identifying the actor, or by judging the behaviour?** The whole scenario is "who, not what." Either verdict reached without checking the documentation is unverified.
- **FP vs. benign precision.** "Rule fired on sanctioned tooling" (FP) vs. vague "looks fine" (benign). Drives tuning decisions.
- **Did they avoid BOTH traps?** Escalating on the scary session *and* waving it through on the account name are both failures; the strong answer verifies.
- **The SCN-011 contrast.** Strong students explicitly pair them and name the deciding difference (verified actor legitimacy).

## MITRE ATT&CK mapping

None. This is sanctioned backup tooling; mapping it to T1005/T1530 (data collection) would itself be the analyst error the scenario teaches against — the technique pattern is present, the adversary intent is not.

## Real-world parallel

Newly-deployed backup/EDR/DLP/inventory agents tripping "mass file access," "data staging," or "off-hours service login" detections is one of the most common FP waves a SOC sees right after any rollout — the tool is legitimate but unfamiliar, and its behaviour is byte-for-byte what exfil prep looks like. Mature SOCs resolve these by *actor identification against change/asset records*, not behavioural reasoning, and they feed the new service account into the known-inventory so it stops being a cold triage. Paired with SCN-011 (same shape, real takeover) it teaches the single highest-leverage instinct for this whole class: the verified legitimacy of the actor — not the alarming behaviour — carries the verdict.
