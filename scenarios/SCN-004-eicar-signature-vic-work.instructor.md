# SCN-004 — Instructor Companion

## Scenario summary

The workstation `vic-work` repeatedly retrieves the EICAR known-malware test file from an internal web host; Wazuh raises a low-severity malware-signature alert. Correct verdict: **true positive** — a host pulling a known-malware-signature file is a real indicator. The lesson is that **low severity is not a reason to dismiss**.

## Learning objectives

- Recognize a malware-signature/IOC alert and not rationalize it away because the artifact is "just a test file" or "low severity."
- Practice the disposition of a *low-severity true positive*: escalate and check the endpoint, don't close-as-noise.
- Identify EICAR and understand why it exists and what its presence on a host means operationally.
- Form correct next steps for a possibly-staged endpoint (isolate/scan/escalate).

## Required prior knowledge

- What an antivirus signature / malware IOC is.
- What EICAR is (or the instinct to look it up rather than guess).
- True positive vs. false positive vs. benign; the idea that severity ≠ verdict.

## Estimated timing

- **Student work:** 10–20 minutes
- **Class debrief:** 10 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** A malware-signature rule fired for `vic-work`, repeatedly, for a request to `/eicar.com` on the internal web host. Source host `10.50.10.20` (vic-work).

2. **Identify the artifact.** The file is the EICAR string. A student who doesn't know it should *look it up* — that instinct is part of the assessment. EICAR is a deliberately-inert industry test file that every AV flags; it is harmless to execute but its presence/retrieval is a real detection.

3. **Resist the "only a test file ⇒ false positive/benign" trap.** The rule did not misfire — `vic-work` genuinely fetched a file matching a known-malware signature, repeatedly. Whether the *payload* is dangerous is a different question from whether the *event* is a true positive. It is a true positive; it is simply low severity.

4. **Open the IRIS case.** Observables: the downloading host `10.50.10.20` and the web host `vic-web`. Confirm/add.

5. **Enrich.** AbuseIPDB on the source in Cortex — RFC1918, empty (the recurring habit-not-dead-end point).

6. **Set the verdict.**
   - Verdict: `true positive`.
   - Severity: `low` — the EICAR artifact is inert / would be blocked by a real AV; defensibly `medium` if you weight "why is a workstation pulling malware at all"; ±1 credited.
   - Confidence: `high` — EICAR is unambiguous.
   - Summary: vic-work repeatedly retrieved the EICAR known-malware signature from the internal web host; low severity but a real indicator; escalate and check the endpoint.

7. **Next steps.** Isolate or scan `vic-work`, escalate to Tier 2 to find *why* the workstation fetched it and whether anything else was pulled. The point is the *process* — a real low-and-slow stager looks exactly like this until you investigate.

## Common student errors

1. **"It's EICAR / a test file ⇒ false positive."** The single defining error of this scenario. Conflates "inert payload" with "not a real detection."
   *Redirect:* "Did the rule fire on something that wasn't there, or did vic-work really request a known-malware-signature file? Which of those is a false positive?"

2. **"Low severity ⇒ close it."** Treats the severity field as the verdict.
   *Redirect:* "Severity tells you how bad it is *if* real. Is it real? What's the verdict, independent of severity?"

3. **Closes benign without checking the endpoint.** Accepts it as a true positive but recommends no action because "nothing bad can happen with EICAR."
   *Redirect:* "You don't know it was EICAR until you investigated — to the workstation, it pulled *malware*. What should happen to a host that just did that?"

4. **Over-escalates to high/critical.** Equally wrong in the other direction — treats a blocked test file like an active breach.
   *Redirect:* "What is the actual impact of *this* artifact? Calibrate: real indicator, low impact — what severity is that?"

## Discussion questions

1. Why does EICAR exist, and what does it let you test that real malware can't safely test?
2. A real malware stager and this EICAR fetch produce a similar alert shape. What would distinguish them, and would your *verdict* differ or only your *severity*?
3. Your SOC gets 200 low-severity malware-signature alerts a day. What triage process keeps you from either drowning or rubber-stamping them closed?
4. The workstation *initiated* the download. What follow-up question does that raise that the alert itself doesn't answer?
5. Where is the line between "false positive" and "true positive, low severity"? State it in one runbook sentence.

## Stretch challenges

- Propose where a real AV/EDR signal would augment this detection, and what the Wazuh integration would look like.
- Design a triage rule of thumb for low-severity malware-signature alerts that neither auto-closes nor auto-escalates.

## Auto-grading rubric (from `SCN-004-eicar-signature-vic-work.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `high` (±1 step credited) | 5 |
| Required observables present (downloading host, vic-web) | 15 |
| Summary contains malware/EICAR and escalate/do-not-dismiss keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they look EICAR up, or guess?** The willingness to identify an unknown artifact rather than assume is the core Tier-1 habit being assessed.
- **Did they separate severity from verdict?** Listen for "real detection, low impact" (good) vs. "low sev so probably nothing" (the trap).
- **Did they still recommend endpoint action?** A true positive that ends with "no action" is an incomplete triage even at low severity.
- **Tone/calibration.** Neither "it's just EICAR lol" nor "CRITICAL breach." A measured low-severity-true-positive write-up is the target.

## MITRE ATT&CK mapping

- **T1105 — Ingress Tool Transfer.** A host retrieving a file (here, a known-malware-signature file) from a remote location — the technique this scenario detects, independent of whether the specific payload is live.

## Real-world parallel

EICAR retrieval/quarantine alerts are a daily reality in every SOC — security tooling and researchers trip them constantly, and the overwhelming majority are noise. That is precisely why this scenario matters: the muscle that closes the 199 benign EICAR hits *without* also reflexively closing the 1 that was a real stager pulling a payload that EICAR was standing in for during a test, or a compromised host beaconing to a malware host that happened to also serve a test file. The discipline — *low severity is a priority, not a verdict; a host pulling a malware-signature file gets looked at* — is the entire point, and pairing it as the library's deliberate low-severity TP teaches students not to let the severity column do their thinking.
