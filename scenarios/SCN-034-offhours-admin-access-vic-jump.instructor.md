# SCN-034 — Instructor Companion

## Scenario summary

An on-call administrator uses a documented break-glass procedure to SSH into `vic-jump` off-hours via the privileged `breakglass` account, runs routine system-state checks, and disconnects. It looks like a privileged intrusion until the analyst verifies the matching change/break-glass record. Correct verdict: **benign** — verified authorized emergency access.

## Learning objectives

- Resist the "off-hours + privileged + unfamiliar account = compromise" reflex; treat it as a hypothesis to verify, not a verdict.
- Use change / incident management as a triage data source — the decisive evidence here lives *outside* the SIEM.
- Distinguish authorized administrative activity from an intruder using a valid account (the SCN-001 contrast: same "successful login," opposite verdict).
- Calibrate confidence when a benign verdict rests on out-of-band documentation and the absence of malicious follow-on.

## Required prior knowledge

- SSH authentication; what a "successful authentication" Wazuh alert (5715) means.
- The concept of break-glass / emergency-access procedures and change management.
- True positive vs. false positive vs. benign; the role of context in triage.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Wazuh rule 5715 ("sshd: authentication success") on `vic-jump`, account `breakglass`, source `10.50.10.250`, off-hours. A single clean success — **no** 5760 failure burst, **no** 5763 brute force, **no** 40112 compromise correlation.

2. **Form the hypothesis, don't jump.** Off-hours privileged access by an unrecognized account is *suspicious* — it is not, by itself, *malicious*. The job is to find evidence that decides it.

3. **Pivot to post-auth activity.** The archives / `vic-jump` logs show `uptime`, `df -h`, `systemctl is-active ssh` — system-state inspection, no changes, no recon-of-an-attacker (`id`, `sudo -l`, wordlists), no lateral movement. This is consistent with operational triage, not intrusion.

4. **Pivot to change management.** The ticket references `CHG-2026-0518-EMG`, explicitly *unvalidated*. The analyst verifies it: is there a genuine, current break-glass / change record for `breakglass` on `vic-jump` in that window, opened by a real on-call engineer? Verifying it (not taking the SIEM's auto-correlation at face value) is the decisive step.

5. **Open the IRIS case.** Observables: source IP `10.50.10.250`, hostname `vic-jump`, user `breakglass`. Confirm/add.

6. **Enrich the source.** Run AbuseIPDB in Cortex on `10.50.10.250` — RFC1918, returns empty (the SCN-001/010 teaching point: enrichment is a habit; empty is expected here, not a dead end).

7. **Set the verdict.**
   - Verdict: `benign` — verified authorized emergency access.
   - Severity: `low` (defensibly `medium`; ±1 credited) — authorized, no impact, but off-hours privileged access is worth a note.
   - Confidence: `medium` — rests on the documentation being genuine and on absent malicious follow-on.
   - Summary: clean off-hours break-glass login, verified against CHG-2026-0518-EMG, routine post-auth, no compromise indicators.

8. **Next steps & close.** Verify with change management, document the verification, close benign. Optionally recommend that break-glass accounts be added to the analyst inventory so this isn't a cold triage next time.

## Common student errors

1. **Escalates on "off-hours + privileged + unknown account" alone.** Pattern-matches to compromise and never checks change management.
   *Redirect:* "What single piece of evidence would flip this from 'looks bad' to 'fine'? Where does that evidence live — is it in Wazuh?"

2. **Takes the SIEM's auto-correlation at face value → closes benign without verifying.** The brief says the CHG link is *unvalidated*; trusting it blindly is the same failure as ignoring it, in the other direction.
   *Redirect:* "The ticket says that correlation isn't validated. What would *you* do to validate it, and what if the record didn't exist?"

3. **Confuses this with SCN-001 (valid account = compromise).** "An attacker with stolen creds also produces a clean 5715" — true, which is why the post-auth behavior and the change record matter.
   *Redirect:* "What did the session actually *do*? Compare it to what the SCN-001 attacker did after logging in."

4. **Rates confidence `high`.** A benign verdict resting on out-of-band docs and an absence of bad follow-on is not high-confidence.
   *Redirect:* "What are you trusting that you didn't directly observe in the SIEM? Does that deserve high confidence?"

5. **Marks FP instead of benign.** The rule fired correctly on a real successful privileged login — it is not a misfire. It's benign activity, not a false positive.
   *Redirect:* "Did the detection malfunction, or did it correctly report real, authorized activity? Which of those is 'benign' vs 'false positive'?"

## Discussion questions

1. An attacker who phished the on-call engineer's break-glass credential would produce nearly this exact telemetry. What additional control or signal would let you tell them apart, and where is it missing here?
2. The decisive evidence was in change management, not the SIEM. What does that imply about Tier-1 tooling and access?
3. Where is the FP/benign line in your own words? Use this scenario and SCN-002 (authorized scan) as the two reference points.
4. The `breakglass` account was unknown to the day shift. Whose process failure is that, and how would you fix it so the next analyst isn't triaging blind at 3 AM?
5. How would your verdict change if the post-auth commands had included `id; sudo -l; cat /etc/shadow`?

## Stretch challenges

- Propose a Wazuh rule (or enrichment) that annotates logins by accounts tagged "break-glass" so the analyst sees the context inline instead of cold.
- Design the minimal change-management field set that would let this be safely auto-triaged, and argue why auto-closing it would still be risky.

## Auto-grading rubric (from `SCN-034-offhours-admin-access-vic-jump.yml`)

| Criterion | Points |
|---|---|
| Verdict = `benign` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (source IP, vic-jump, breakglass) | 15 |
| Summary contains break-glass/authorized and benign/verified keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they actually verify, or just trust/ignore the CHG link?** The whole scenario is about the verification step. A student who closed benign because "the ticket said so" got the right answer for the wrong reason — call it out.
- **Hypothesis discipline.** Did they treat "compromise" as a hypothesis to test, or as a starting verdict they reluctantly abandoned? Listen to the order of their reasoning.
- **The SCN-001 contrast.** Strong students explicitly note "same successful-login signal as SCN-001, opposite verdict, because behavior + authorization differ." That comparison is the learning.
- **Summary quality.** Could a Tier 2 lead see in 20 seconds *what* happened, *that it was verified*, and *against what record*? The "verified against X" clause is the one weak students omit.

## MITRE ATT&CK mapping

None. This scenario is authorized administrative activity; mapping benign ops to ATT&CK techniques would itself be an analyst error worth discussing (technique ≠ intent).

## Real-world parallel

Every mature SOC sees this weekly: an on-call engineer invokes break-glass at 3 AM to fix a production incident, the privileged login fires, and Tier 1 must decide fast without waking anyone. The failure mode is bimodal and both directions are real incidents: analysts who reflexively escalate burn the on-call's night and erode trust in the SOC; analysts who reflexively wave through "probably just ops" are exactly how attackers using stolen/abused privileged credentials slip past Tier 1. The discipline being taught — *verify the authorization out-of-band, every time, even when it's almost certainly fine* — is the same control that catches the one time it isn't.
