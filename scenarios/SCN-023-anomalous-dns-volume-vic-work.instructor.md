# SCN-023 — Instructor Companion

## Scenario summary

A sustained, low-rate stream of DNS queries from `vic-work` to a single external domain, flagged by Suricata as possible DNS tunneling/exfiltration. No single query is suspicious — the verdict requires aggregate/time-window reasoning. Correct verdict: **true positive** (low-and-slow data exfiltration over DNS). This is v1.0's "hard one": it teaches statistical thinking, not signature-spotting.

## Learning objectives

- Reason from an *aggregate pattern over time*, not a single event — the core advanced-triage skill.
- Recognize DNS as an exfiltration/C2 channel and why low-and-slow defeats volume-threshold instincts.
- Make a confident escalation under incomplete certainty (Tier 1 contains; Tier 2 confirms payload).
- Resist "each query is fine ⇒ benign" — the exact reasoning DNS tunneling exploits.

## Required prior knowledge

- How DNS works and why it is almost always allowed outbound.
- The concept of covert channels / data exfiltration.
- That "no single event is bad" can still sum to a true positive (rate/volume/timing analysis).

## Estimated timing

- **Student work:** 25–40 minutes
- **Class debrief:** 20 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert and its category.** Suricata "ET TROJAN Possible DNS Tunneling Outbound Data Exfiltration", category "A Network Trojan was detected", source `vic-work` (10.50.10.20) → `203.0.113.53:53/udp`. Note: the signature already names the hypothesis.

2. **Look at the pattern, not the packet.** Pull the query stream over the window: sustained, low-rate, single destination, over a long period. That *shape* — not any one query — is the evidence. A student who opens one DNS event and shrugs has missed the point.

3. **Name the technique.** DNS is allowed egress nearly everywhere; encoding data into queries to a controlled domain is the canonical low-and-slow exfil/C2. Low rate is a *deliberate* evasion of volume thresholds, not exculpatory.

4. **Open the IRIS case.** Observables: source `vic-work` (10.50.10.20), destination `203.0.113.53` (and the domain if surfaced). Confirm/add. Enrich the destination (RFC range → empty in-lab; the *pattern + signature* carry the verdict, the enrichment is the habit).

5. **Set the verdict.**
   - Verdict: `true positive` — low-and-slow DNS exfiltration / covert channel.
   - Severity: `high` — probable active data loss / established channel.
   - Confidence: `medium` — the pattern + NIDS verdict are strong, but full payload/volume confirmation is Tier 2 work; Tier 1 acts now, doesn't wait for certainty.
   - Summary: sustained low-rate single-destination DNS from vic-work; NIDS-flagged tunneling/exfil; contain + escalate.

6. **Next steps.** Contain `vic-work`, block the destination domain/resolver path, escalate to Tier 2 to scope what and how much left and for how long.

## Common student errors

1. **"Each DNS query is normal ⇒ benign/FP."** The defining trap; it is exactly the reasoning DNS tunneling is designed to exploit.
   *Redirect:* "Stop looking at one query. Plot them over the hour. What does the *pattern* look like, and what is it for?"

2. **Waits for certainty before escalating.** "Can't prove data left, so I'll monitor."
   *Redirect:* "If this is exfil, what does 'monitor' cost you? What can Tier 1 do now that doesn't require proving the payload?"

3. **Under-rates severity** ("just DNS").
   *Redirect:* "What is the impact if this is what the signature says? Calibrate to that, with confidence reflecting your uncertainty — don't lower severity to match low confidence."

4. **Treats low rate as exculpatory.** "Only a few queries an hour, can't be exfil."
   *Redirect:* "Why would an attacker keep it slow? What is low-and-slow optimised to defeat — and is that your detection?"

5. **Stops at the signature, doesn't characterise the pattern.** Writes "TP, Suricata said tunneling" with no aggregate analysis.
   *Redirect:* "Convince a skeptical Tier 2 in your summary using the *pattern*, not just 'the rule said so.'"

## Discussion questions

1. What query-stream features distinguish DNS tunneling from a chatty-but-legitimate client (CDN, telemetry, DoH bootstrap)? Where would each be ambiguous?
2. The attacker chose low-and-slow. What detection strategy beats that, and what's its false-positive cost?
3. Tier 1 escalates at medium confidence here. Argue for and against contain-now vs. confirm-first; what tips it?
4. If the destination domain enriched as a major CDN, would your verdict change, or your confidence, or neither?
5. How would your write-up differ for an audience of (a) the asset owner vs. (b) Tier 2 IR?

## Stretch challenges

- Specify the Wazuh/Suricata analytics (rates, unique-subdomain entropy, NXDOMAIN ratio, time-of-day) that would detect this without the bundled signature, and discuss FP cost.
- Design the containment that stops exfil without tipping the attacker, and the trade-offs.

## Auto-grading rubric (from `SCN-023-anomalous-dns-volume-vic-work.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `high` (±1 step → `medium`/`critical` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (vic-work, destination) | 15 |
| Summary contains DNS-tunneling/exfil and exfiltration/escalate keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they reason about the aggregate pattern, or one event?** This is the entire point of the scenario and the single best discriminator of advanced readiness.
- **Did they escalate under uncertainty?** Look for "high severity, medium confidence, contain now" — the mature posture — vs. "monitor until sure."
- **Quality of the persuasive summary.** Advanced triage includes convincing Tier 2 with the pattern. Weak summaries cite only the signature.
- **Did they resist the low-and-slow trap consciously?** Strong students name it ("low rate is the evasion, not the exoneration").

## MITRE ATT&CK mapping

- **T1048.003 — Exfiltration Over Unencrypted/Alternative Protocol.** Data leaving over DNS rather than the expected channel.
- **T1071.004 — Application Layer Protocol: DNS.** DNS abused as the application-layer carrier for the covert channel/C2.

## Real-world parallel

DNS exfiltration/tunneling is a long-documented, still-current technique (iodine/dnscat-style tooling; multiple APT and commodity campaigns have used DNS for C2 and staged data theft precisely because egress DNS is rarely restricted or inspected). It is the canonical "no single event is malicious, the aggregate is" case — which is why it earns the v1.0 "hard one" slot: it forces the student off signature-spotting and onto statistical/temporal reasoning and decisive escalation under incomplete certainty, the exact skills that separate a Tier-1 who can grow into IR from one who only closes obvious tickets.
