# SCN-008 — Instructor Companion

## Scenario summary

Suricata flags an internal host sweeping ports across the victim subnet. It looks like reconnaissance/lateral movement — but the source is the documented internal monitoring/VA host doing its scheduled job. Correct verdict: **false positive**, resolved by checking the source against the asset inventory.

## Learning objectives

- Triage *internal* scan alerts: the verdict hinges on the *source's* identity, not the scan behaviour.
- Use the asset inventory / documented-scanner list as the deciding data source.
- Distinguish a false positive (rule fired on sanctioned activity) from benign and from a real internal recon TP.
- Reinforce the SCN-007/SCN-017 lesson: with NIDS alerts, the *endpoint reputation/role* carries the verdict.

## Required prior knowledge

- What a port scan is and why both attackers and VA/monitoring tools do it.
- NIDS scan signatures; internal vs. external direction.
- False positive vs. benign vs. true positive.

## Estimated timing

- **Student work:** 10–20 minutes
- **Class debrief:** 10 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Suricata "ET SCAN Behavioral Internal Port Scan", source `10.50.10.5`, sweeping the subnet (e.g., `10.50.10.20`). Internal→internal.

2. **Ask "who is the source?" before "is scanning bad?"** A scan from an unknown internal host is lateral-movement recon (TP). A scan from the VA scanner is its job (FP). The behaviour is identical; the source identity decides.

3. **Check the asset inventory — the deciding step.** `10.50.10.5` is the documented internal monitoring/vulnerability host. Subnet sweeps are its sanctioned function.

4. **Open the IRIS case.** Observables: source `10.50.10.5`, a scanned destination `10.50.10.20`. Confirm/add.

5. **Set the verdict.**
   - Verdict: `false positive` — rule fired on documented, sanctioned activity.
   - Severity: `low`.
   - Confidence: `medium` — rests on the inventory being authoritative and current.
   - Summary: internal port sweep from 10.50.10.5; source is the documented monitoring/VA host; FP; tune/allowlist.

6. **Next steps.** Document/confirm the scanner in the inventory, allowlist or tune for the known source, close as false positive.

## Common student errors

1. **"Internal port scan ⇒ lateral movement ⇒ TP."** Pattern-matches the behaviour, skips the source check.
   *Redirect:* "Who is 10.50.10.5? What would a scan from your VA scanner look like — and how is that different from this?"

2. **Doesn't consult the inventory; guesses either way.** Right answer for the wrong reason if not verified.
   *Redirect:* "What single source of truth tells you whether that host is a sanctioned scanner? Did you check it?"

3. **Marks benign rather than false positive.** Legitimate activity that *tripped a rule* is an FP; precision matters for tuning/metrics.
   *Redirect:* "Did the rule fire on something that wasn't an attack? What's that called, exactly?"

4. **Closes FP but recommends no tuning.** Leaves the SOC to re-triage the same scheduled scan forever.
   *Redirect:* "This scanner runs on a schedule. What should happen so the next analyst doesn't burn 20 minutes on it again?"

## Discussion questions

1. SCN-007/017/008 are all NIDS alerts. Across them, what single attribute most often decides the verdict, and why?
2. An attacker who compromised the VA scanner would scan from a documented source. What additional signal distinguishes that from normal VA activity?
3. What's the operational cost of (a) escalating every VA scan vs. (b) blanket-allowlisting the scanner source?
4. Internal-source vs. external-source scan: how does each change the likely story and the urgency?
5. Where's the FP/benign line here, in one runbook sentence?

## Stretch challenges

- Write the Suricata/Wazuh suppression for the documented scanner source and discuss the lateral-movement blind spot it creates (compromised-scanner case).
- Propose a detection that would catch a *non-scheduled* or *off-target* scan from the otherwise-legitimate scanner.

## Auto-grading rubric (from `SCN-008-internal-port-scan-vic-net.yml`)

| Criterion | Points |
|---|---|
| Verdict = `false_positive` | 50 |
| Severity = `low` (±1 step → `medium` credited) | 15 |
| Confidence = `medium` (±1 step credited) | 5 |
| Required observables present (source IP, a scanned dest) | 15 |
| Summary contains scan/scanner and FP/documented keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they check the source against the inventory, or judge the scan behaviour?** The whole scenario is "identify the source first." A verdict reached without the inventory is unverified.
- **FP vs. benign precision.** "Rule fired on sanctioned documented activity" (FP) vs. vague "it's fine" (benign). The distinction drives tuning.
- **Did they recommend tuning?** A closed FP with no follow-up is an incomplete disposition for a *recurring scheduled* trigger.
- **The NIDS-cluster pattern.** Strong students articulate "for these network alerts, source/destination reputation decided it, not the traffic shape" across SCN-007/017/008.

## MITRE ATT&CK mapping

None. This is sanctioned internal vulnerability/monitoring scanning; attributing it to T1046 (Network Service Discovery) would be the analyst error the scenario teaches against — the technique pattern is present, the adversary intent is not.

## Real-world parallel

Internal scan alerts from the org's own VA scanner (Nessus, Qualys, Rapid7), monitoring (Zabbix, Nagios), or asset-discovery tooling are a perennial top-FP in every SOC. Mature teams allowlist the documented scanner sources precisely so this doesn't consume Tier-1 time — and the residual risk (a compromised scanner, or scanning outside its sanctioned scope/schedule) is a known, deliberately-accepted trade handled by higher-tier detections, not by Tier-1 escalating every sweep. Paired with SCN-007 (external known-bad, TP) and SCN-017 (behavioural beacon to allowlisted SaaS, FP), this completes the core network-triage instinct: resolve the endpoint identity first.
