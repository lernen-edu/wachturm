# SCN-007 — Instructor Companion

## Scenario summary

Suricata flags an outbound connection from `vic-work` to a known Tor exit node ("ET TOR Known Tor Exit Node Traffic"). A single NIDS alert whose signature is itself the threat-intel hit. Correct verdict: **true positive** — a workstation reaching known anonymizer/exit-node infrastructure is C2/exfil-shaped, not normal user activity.

## Learning objectives

- Read and trust a NIDS signature: the rule text and category often *are* the intel.
- Triage a network/Suricata alert (not just host/Wazuh alerts) and pivot on a destination IP.
- Recognize outbound-to-known-bad as a high-value indicator even from a single alert.
- Calibrate severity for "strong indicator, impact not yet confirmed."

## Required prior knowledge

- What Tor / an anonymizing exit node is, and why workstation→Tor outbound is abnormal.
- NIDS vs. HIDS (Suricata produces this, not a host log).
- True positive vs. false positive vs. benign.

## Estimated timing

- **Student work:** 10–20 minutes
- **Class debrief:** 10 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** A Suricata alert: `vic-work` (10.50.10.20) → 198.51.100.66, signature "ET TOR Known Tor Exit Node Traffic group 1", category "A Network Trojan was detected". This is a NIDS alert — note the data source.

2. **Read the signature, don't just see "alert."** The ET ruleset already did the attribution: the destination is a known Tor exit node. The intel is in the signature; the analyst's job is to recognize and act on it, not re-derive it.

3. **Pivot on the destination.** Add `198.51.100.66` as an observable; enrich in Cortex. (Sealed lab: RFC5737 documentation IP, enrichment is empty — the recurring point that the *signature* carries the verdict here, the enrichment is the habit.)

4. **Reason about direction and host.** *Outbound*, *initiated by a workstation*, to *anonymizing infrastructure*. That is not a user browsing — it is C2, exfil staging, or a serious policy/tooling violation. None of those is "close it."

5. **Open the IRIS case.** Observables: destination `198.51.100.66`, source `vic-work` (10.50.10.20). Confirm/add.

6. **Set the verdict.**
   - Verdict: `true positive`.
   - Severity: `medium` — strong indicator; what the channel carried isn't yet confirmed (defensibly `high` if treated as confirmed C2; ±1 credited).
   - Confidence: `high` — the signature is an unambiguous IOC.
   - Summary: NIDS flagged vic-work outbound to a known Tor exit node; C2/exfil-shaped; block + isolate + escalate.

7. **Next steps.** Block the destination, isolate/scan `vic-work`, escalate to Tier 2 to scope what the channel carried and for how long.

## Common student errors

1. **Treats it as benign "maybe a user used Tor Browser."** Possible in theory, but a workstation in a managed environment reaching a Tor exit node is policy-violating at best and C2 at worst — not a close-it.
   *Redirect:* "Even if it were Tor Browser, is unsanctioned anonymizer use on a managed workstation something you close silently? And how would you tell that apart from C2 from this alert alone?"

2. **Distrusts the signature / "needs more proof."** Waits for impossible corroboration and under-rates a clear IOC.
   *Redirect:* "What did the ruleset already tell you about that IP? How much more certain does 'known Tor exit node' need to be?"

3. **Ignores it because it's a Suricata/NIDS alert, not a familiar host alert.** Tier 1s over-anchored on Wazuh host alerts sometimes deprioritize network alerts.
   *Redirect:* "Where did this alert come from, and why might a network alert see something a host log wouldn't?"

4. **Over-calls critical with no scoping.** Jumps to "confirmed breach" without noting impact is unconfirmed.
   *Redirect:* "What do you actually know was sent? Severity reflects confirmed impact plus indicator strength — calibrate."

## Discussion questions

1. The signature did the attribution for you. When *should* you distrust a NIDS signature, and how would you validate one?
2. Outbound to Tor vs. inbound from Tor — how do the triage and the likely story differ?
3. What host-side (Wazuh) evidence would you want to correlate with this NIDS alert, and what would each tell you?
4. If this were a server instead of a workstation, would your verdict or severity change? Why?
5. The lab simulates the NIDS event. In a real deployment, what produces this alert and what are its common benign causes (and how many are there really, for *workstation→Tor*)?

## Stretch challenges

- Sketch the Wazuh correlation that would tie this Suricata alert to a process on `vic-work` (what host telemetry is required).
- Propose the block: where in the network would you enforce it, and what's the collateral risk of blocking Tor wholesale?

## Auto-grading rubric (from `SCN-007-outbound-flagged-ip-vic-work.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `medium` (±1 step → `low`/`high` credited) | 15 |
| Confidence = `high` (±1 step credited) | 5 |
| Required observables present (destination IP, vic-work) | 15 |
| Summary contains Tor/known-bad and outbound/C2 keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they read the signature?** The whole scenario is "the intel is in the alert text." A student who escalated without articulating *why the destination is bad* got there by vibe.
- **Direction awareness.** Did they note it was *outbound*, *workstation-initiated*? That framing is what makes it C2-shaped rather than "scan noise."
- **Severity reasoning.** "Strong indicator, impact unconfirmed → medium, escalate to scope" is the calibrated answer; both "meh, low" and "CRITICAL breach" miss.
- **Did they treat the NIDS alert as first-class?** Watch for deprioritizing it because it isn't a host log.

## MITRE ATT&CK mapping

- **T1090.003 — Proxy: Multi-hop Proxy.** Tor is the canonical multi-hop anonymizing proxy; outbound to an exit node is this technique's network signature.
- **T1571 — Non-Standard Port.** The connection to the exit node on 9001 (a common Tor ORPort) — reinforces "not ordinary web traffic."

## Real-world parallel

Workstation-to-Tor is a recurring real SOC alert with a bimodal cause: unsanctioned privacy tooling by an employee, or malware using Tor for resilient C2 (a long-standing technique across commodity and targeted families). Both are dispositioned the same way at Tier 1 — investigate the endpoint and escalate — which is the lesson: a single high-quality NIDS signature about *known-bad infrastructure* is enough to act on, and "it might be benign" is not a close. The scenario also forces the network-alert muscle: Tier 1s who only ever look at Wazuh host alerts miss exactly this class.
