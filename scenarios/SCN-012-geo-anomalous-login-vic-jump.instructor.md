# SCN-012 — Instructor Companion

## Scenario summary

A known user, `awilson`, logs into `vic-jump` cleanly from a source that geolocates outside their normal region, then does ordinary work. It looks like impossible-travel account compromise until the analyst verifies a genuine travel/helpdesk record and benign post-auth activity. Correct verdict: **benign** — verify-and-close. This is the BN counterpart to SCN-011 (same 5715 success; the record and the behaviour decide it).

## Learning objectives

- Treat a geo-anomaly as an investigation trigger, not a verdict.
- Practice the verify-and-close pattern: the deciding evidence is an out-of-band record, not the alert.
- Hold the discipline of *actually verifying* the auto-correlated note rather than trusting or ignoring it (the SCN-034 lesson, reused).
- Complete the SCN-011 ↔ SCN-012 ↔ SCN-034 triad: same-shaped login alert, three different dispositions decided by context + behaviour.

## Required prior knowledge

- SSH auth; the meaning of a Wazuh "authentication success" (5715) alert.
- The concept of impossible-travel / geo-velocity anomalies.
- True positive vs. false positive vs. benign; verify-and-close triage.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Wazuh 5715 on `vic-jump`, user `awilson`, source `10.50.10.250`, off-region. No 5760 burst, no 5763/40112 — not brute force.

2. **Name the anomaly, withhold the verdict.** "Login from an unexpected country" is the impossible-travel pattern — a strong *prompt*, not a conclusion. Both a compromised account and a travelling employee produce exactly this.

3. **Pivot into the session.** `whoami; ls ~; cat ~/notes.txt; uptime` — the user's own files, no recon, no persistence, no sensitive-data staging. This is consistent with the real user working, not an intruder (contrast SCN-011's recon + financials read + planted key).

4. **Verify the travel/helpdesk record — the decisive step.** The ticket cites a travel note, explicitly *unvalidated*. The analyst confirms a genuine, current travel/helpdesk record for `awilson`, that region, that window. Verifying it (not trusting the SIEM's auto-correlation, not ignoring it) is the whole exercise.

5. **Open the IRIS case.** Observables: source IP `10.50.10.250`, hostname `vic-jump`, user `awilson`. Confirm/add.

6. **Enrich the source.** AbuseIPDB in Cortex — RFC1918, empty (the recurring teaching point: habit, not a dead end; in this lab the geo-claim is narrative, so the verification is the human/record step, not the analyzer).

7. **Set the verdict.**
   - Verdict: `benign` — verified legitimate user travelling.
   - Severity: `low` (defensibly `medium`; ±1 credited).
   - Confidence: `medium` — rests on the travel record being genuine and absent malicious follow-on.
   - Summary: clean off-region login for a known user, verified against the travel/helpdesk record, ordinary post-auth, no compromise indicators.

8. **Next steps & close.** Confirm with helpdesk, document the verification, close benign. Optionally recommend the user's travel be pre-registered so this isn't a cold triage next time.

## Common student errors

1. **Escalates on the geo-anomaly alone.** "Login from another country = compromised" — closes TP without checking records or behaviour.
   *Redirect:* "What legitimate, common situation produces exactly this signal? How would you tell it apart from compromise?"

2. **Trusts the SIEM's auto-correlated travel note blindly → closes benign without verifying.** Same failure as SCN-034 error #2: the note is explicitly unvalidated.
   *Redirect:* "The ticket says that note isn't validated. What do *you* do to confirm it, and what if there were no such record?"

3. **Confuses it with SCN-011.** Both are clean logins from an unusual source; the student applies SCN-011's TP reasoning without checking that the record exists and the behaviour is benign here.
   *Redirect:* "Compare the post-auth activity to SCN-011's. What did awilson actually do, and is there a record SCN-011 didn't have?"

4. **Marks FP instead of benign.** The rule fired correctly on a real successful login; it is not a misfire.
   *Redirect:* "Did the detection malfunction, or correctly report real, authorized activity? Which is 'benign' vs 'false positive'?"

5. **Rates confidence `high`.** A benign verdict resting on an out-of-band record and absent bad behaviour isn't high-confidence.
   *Redirect:* "What are you trusting that you didn't directly observe? Does that deserve high confidence?"

## Discussion questions

1. SCN-011, SCN-012, and SCN-034 produce nearly the same login alert. Rank the signals that separate them by how decisive each is.
2. An attacker who stole `awilson`'s credentials *and* knew they were travelling could mimic this almost perfectly. What additional signal would still catch them?
3. The decisive evidence was a helpdesk/travel record. What does that say about what Tier 1 needs access to?
4. How should your verdict change if the travel record existed but the session had also run `cat /etc/shadow` and appended an SSH key?
5. Where exactly is the FP/benign line? Use SCN-002 (authorized scan, FP) and this scenario (benign) as the two anchors.

## Stretch challenges

- Design the minimal travel-registration data that would let this be safely auto-triaged, and argue why auto-closing it is still risky.
- Propose an enrichment that would make the geo-claim real in a non-sealed deployment, and discuss its false-positive profile (VPNs, CDNs, mobile carriers).

## Auto-grading rubric (from `SCN-012-geo-anomalous-login-vic-jump.yml`)

| Criterion | Points |
|---|---|
| Verdict = `benign` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (source IP, vic-jump, awilson) | 15 |
| Summary contains travel/verified and benign/no-compromise keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they verify, or trust/ignore the note?** The scenario is the verification step. "Closed benign because the ticket said travel" is the right answer for the wrong reason — call it out.
- **Hypothesis discipline.** Did they treat "compromise" as a hypothesis to disprove, or jump to it and grudgingly retreat? Order of reasoning matters.
- **The triad comparison.** Strong students explicitly position this against SCN-011/SCN-034. That comparison is the learning objective.
- **Summary quality.** Could Tier 2 see in 20 seconds: who, from where, *that it was verified and against what*? The "verified against X" clause is what weak students drop.

## MITRE ATT&CK mapping

None. This is a legitimate user travelling; mapping benign activity to ATT&CK would itself be an analyst error worth discussing (a geo-anomaly is not a technique).

## Real-world parallel

Impossible-travel / geo-velocity alerts are among the highest-volume identity alerts in any real SOC, and the overwhelming majority are VPNs, mobile roaming, cloud egress, or genuine travel. The skill being taught is the one that keeps a SOC sane: a geo-anomaly is a *question*, answered by verifying identity context out-of-band — not an auto-escalation and not an auto-dismissal. Paired with SCN-011 (same signal, real takeover) it teaches the thing that actually matters: the alert is identical; the verdict lives in the verification and the behaviour.
