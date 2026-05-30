# SCN-017 — Instructor Companion

## Scenario summary

Suricata's behavioural beacon heuristic fires on regular-interval outbound from `vic-work` to a single external endpoint. It looks like C2 — but the destination is a documented, allowlisted cloud-agent endpoint whose heartbeat is periodic by design. Correct verdict: **false positive**. The lesson is "looks suspicious" ≠ "is suspicious," resolved by verifying the allowlist.

## Learning objectives

- Distinguish a behavioural heuristic ("possible periodic beaconing") from a known-bad-destination signature — different strengths of evidence.
- Use the egress/SaaS allowlist as the deciding data source for "is this destination expected?"
- Practice the FP disposition: the rule fired correctly on legitimate activity; document/tune, don't escalate.
- Hold the SCN-007 contrast: same NIDS source, near-identical "outbound to external," opposite verdict — decided by destination reputation/allowlist.

## Required prior knowledge

- What beaconing is and why both C2 and legitimate agents (EDR, monitoring, cloud sync) produce it.
- NIDS behavioural heuristic vs. signature/IOC match.
- False positive vs. true positive vs. benign.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert and the signature *type*.** Suricata: `vic-work` (10.50.10.20) → 203.0.113.200:443, regular interval, signature "ET POLICY Possible Periodic Beaconing Activity Observed", category "Potentially Bad Traffic". Note the words *Possible* and *POLICY* — this is a behavioural heuristic, not "known Tor exit node" (contrast SCN-007).

2. **Resist "beacon ⇒ C2."** Regular-interval outbound is exactly what EDR check-ins, monitoring agents, and cloud-sync clients do. The pattern is necessary but not sufficient for C2.

3. **Pivot on the destination — the deciding step.** Enrich `203.0.113.200` and, crucially, check it against the egress/SaaS allowlist and asset documentation. It is a documented, approved cloud-agent endpoint.

4. **Open the IRIS case.** Observables: destination `203.0.113.200`, source `vic-work` (10.50.10.20). Confirm/add.

5. **Set the verdict.**
   - Verdict: `false positive` — the heuristic fired on legitimate, documented activity.
   - Severity: `low`.
   - Confidence: `medium` — rests on the allowlist being authoritative (an *undocumented* beacon destination would flip this instantly).
   - Summary: behavioural beacon heuristic on vic-work→203.0.113.200; destination is a documented allowlisted cloud-agent endpoint; FP; recommend tuning.

6. **Next steps.** Document/confirm the allowlist entry, recommend tuning the heuristic to suppress the known endpoint, close as false positive.

## Common student errors

1. **"Beaconing ⇒ C2 ⇒ true positive."** Pattern-matches the behaviour to malware without checking the destination.
   *Redirect:* "What else beacons on a regular interval that is completely legitimate? How would you tell those apart from C2 here?"

2. **Doesn't check the allowlist; calls it benign or TP on a guess.** Either direction without the verification is the same failure.
   *Redirect:* "What single source of truth decides whether that destination is expected? Did you consult it?"

3. **Marks benign instead of false positive.** The activity is legitimate *and* the rule fired on it — that is the definition of an FP, not benign-suspicious.
   *Redirect:* "Did the rule fire on legitimate activity that tripped a heuristic? What's that called, precisely — and how does it differ from benign?"

4. **Trusts an auto-enrichment 'clean' verdict without the allowlist.** Cortex/RFC-range emptiness isn't proof of legitimacy here; the allowlist is.
   *Redirect:* "Enrichment came back empty — does empty mean safe? What actually told you this endpoint is approved?"

5. **Over-confident (confidence high).** An FP resting on an allowlist is medium-confidence; allowlists go stale.
   *Redirect:* "What would change your verdict? If that's plausible, is this really high confidence?"

## Discussion questions

1. SCN-007 and SCN-017 are both "workstation → external, NIDS-flagged." Rank the signals that separate TP from FP here, most decisive first.
2. The signature said "Possible." How should the hedged language in a signature change how much corroboration you require?
3. An attacker who beacons *to an allowlisted SaaS* (living-off-trusted-services C2) would look exactly like this. What additional signal would catch that, and is Tier 1 expected to?
4. What's the cost of closing this FP wrong in each direction (escalate vs. ignore), operationally?
5. Where's the line between "false positive" and "benign"? Use SCN-003 (benign) and this scenario (FP) as anchors.

## Stretch challenges

- Write the Suricata/Wazuh suppression or allowlist-aware tuning for this endpoint and discuss the risk it introduces (trusted-destination C2).
- Design a detection that would distinguish a real beacon hidden inside allowlisted-SaaS traffic from the legitimate agent.

## Auto-grading rubric (from `SCN-017-periodic-beacon-vic-work.yml`)

| Criterion | Points |
|---|---|
| Verdict = `false_positive` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (destination IP, vic-work) | 15 |
| Summary contains beacon/heartbeat and FP/documented keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they verify the allowlist, or guess?** The scenario *is* the verification. A correct verdict reached without consulting the allowlist is luck.
- **Heuristic vs. signature awareness.** Did they note this was "Possible/POLICY" behavioural, unlike SCN-007's definitive "known Tor exit node"? That distinction is the core skill.
- **FP vs. benign precision.** Listen for "rule fired on legitimate documented activity" (FP) vs. vague "it's fine" (benign). The precision matters for metrics and tuning.
- **The SCN-007 contrast.** Strong students explicitly pair them. That's the intended learning.

## MITRE ATT&CK mapping

None. This is a legitimate cloud-agent heartbeat; mapping it to C2 techniques would itself be the analyst error the scenario teaches against (a behaviour pattern is not a technique attribution).

## Real-world parallel

"Possible beaconing" heuristics are a top FP source in any NIDS/NDR deployment: EDR agents, telemetry, software updaters, and cloud sync all beacon. SOCs survive this by resolving the destination against an allowlist/inventory, not by reasoning from the pattern alone — and the genuinely hard adversary case (C2 tunnelled through allowlisted SaaS) is explicitly *not* a Tier-1 close-it-as-TP-on-vibes call. Paired with SCN-007 (definitive known-bad destination, TP) this teaches the single most useful network-triage instinct: the *destination's reputation/approval status*, not the traffic shape, carries the verdict.
