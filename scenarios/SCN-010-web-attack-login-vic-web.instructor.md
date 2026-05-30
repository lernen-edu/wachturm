# SCN-010 — Instructor Companion

## Scenario summary

An automated SQL-injection scanner fires a rapid burst of injection payloads at the `/login` endpoint of the public web host `vic-web` from a single source IP, with a `sqlmap`-style User-Agent. This is a true positive: deliberate, automated exploitation activity against an internet-facing service. The correct disposition is escalate-and-block, even though the injection did not succeed.

## Learning objectives

- Recognize a web-application-attack signature in a SIEM (Wazuh rule 31164 "SQL injection attempt", 31106 "A web attack returned code 200").
- Read request artifacts in an alert — URI, query string, User-Agent, request rate — and reason from them.
- Distinguish *"the attack failed"* from *"this is not an attack."* An unsuccessful exploitation attempt is still a true positive.
- Calibrate severity for a real-but-unsuccessful attack against an exposed service (medium, not high; not low/FP).
- Form next steps for hostile web traffic: block the source, review the web logs for anything that *did* succeed, escalate.

## Required prior knowledge

- What SQL injection is, at a conceptual level (untrusted input reaching a query).
- Familiarity with the Wazuh dashboard's Alerts view and how to open an alert's detail.
- True positive vs. false positive vs. benign in alert triage.
- The idea that automated scanners exist and look different from a human.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 10–15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Spot the alert cluster.** In Wazuh's Alerts view: a burst of rule 31103 ("SQL injection attempt") on `vic-web`, escalating to rule 31152 ("Multiple SQL injection attempts from same source"), all from source IP `10.50.10.250`.

2. **Read the request detail.** The alerts carry the offending URIs — `/login?username=admin' OR '1'='1--`, `/login?id=1 UNION SELECT username,password FROM users--` — and a `sqlmap/1.7.2` User-Agent. Two payload families, dozens of requests, one source, ~20-second window. This is a tool, not a person.

3. **Resolve the "did it work?" question correctly.** The alerts tell you an attack *happened* — they do **not** tell you it *succeeded* or *failed*. Rule 31152 ("multiple SQL injection attempts from same source") is the key signal: this is a deliberate, automated wave, not one stray request. Students want the alert to declare the outcome; it doesn't. The core teaching moment: *you disposition this from the attack pattern (unambiguously hostile, automated) and from context about the target — never by assuming success or failure that the alerts don't state.* (For the record: `vic-web` is static nginx with no database, so nothing was extracted — but the analyst should reach "no evidence of success," not "I know it failed.")

4. **Open the auto-created IRIS case.** Observables should include source IP `10.50.10.250` and hostname `vic-web`. Confirm and add any missing.

5. **Identify the source as hostile and enrich it.** `10.50.10.250` is not in the known-good inventory (legit victims are `.10/.20/.30/.40`; benign noise is `.5`). Run AbuseIPDB in Cortex. It is RFC1918-private so enrichment returns empty — the same teaching point as SCN-001: enrichment is a habit, and empty results in this lab are expected, not a dead end.

6. **Set the verdict.**
   - Verdict: `true positive` — deliberate automated exploitation of an exposed endpoint.
   - Severity: `medium` — a real attack attempt, but no evidence of successful compromise (defensibly `low` for a commodity scanner with no impact; the scorer credits ±1 step).
   - Confidence: `high` — the signature is unambiguous.
   - Summary should state: automated SQLi scan, single source, sqlmap UA, `/login` target, no evidence of success, recommend block + escalate.

7. **Define next steps.** Block the source IP at the perimeter, review `vic-web` access logs for any non-200 / anomalous responses that suggest a payload *did* land, escalate to Tier 2 if the host is genuinely internet-exposed (exposure itself is a finding).

8. **Close the case** with summary and next steps populated.

## Common student errors

1. **Assumes the outcome the alerts don't state → over- or under-escalates.** The student decides the injection "must have worked" (escalates critical) or "obviously failed" (dismisses) without evidence either way. The alerts (31103/31152) prove an attack, not its result.
   *Redirect:* "Which alert tells you the injection returned data? It doesn't — so what *can* you conclude, and what would you need to confirm impact?"

2. **"No proof it succeeded, so this is a false positive" → closes FP-low.** The student finds no evidence of compromise and dismisses the whole ticket.
   *Redirect:* "Did the rule fire on something that wasn't an attack? Or did it correctly catch a real attack whose success you can't yet confirm? Which of those is a false positive?"

3. **Recognizes `sqlmap` and concludes "just a pentest tool, FP."** Same tooling-vs-authorization confusion as SCN-001 error #5. Attack tooling against your exposed endpoint without an engagement letter is an attack.
   *Redirect:* "Where would you confirm an authorized test? What does the absence of that record mean here?"

4. **Skips observable enrichment.** Closes without running any Cortex analyzer on the source IP.
   *Redirect:* "If this IP hit three of your other hosts tomorrow, what would you want already on file about it?"

5. **Undersells next steps to "monitor."** A live, automated attacker probing an exposed endpoint warrants blocking now, not watching.
   *Redirect:* "This scanner is running right now. 'Monitor' means you let it keep going — is that what you want?"

## Discussion questions

1. The injection didn't succeed because `vic-web` is static. If `vic-web` were a real app with a database, what would you expect the alerts to look different — and would your *verdict* change, or only your *severity*?
2. Where is the line between "false positive" and "true positive that failed"? Articulate it in one sentence you could put in a runbook.
3. The User-Agent was `sqlmap/1.7.2`. How much should a User-Agent influence your verdict, given it is attacker-controlled and trivially spoofed?
4. This was loud — dozens of requests with obvious payloads in ~20 seconds. How would a more careful attacker change this to evade rule 31164, and what would you need to detect *that*?
5. The brief says vic-web is "the public web host." What follow-up question should that prompt you to ask the asset owner, independent of this specific alert?

## Stretch challenges

- Tune a Wazuh `local_rules.xml` rule that distinguishes a high-rate scanner (many injection requests/second from one source) from a single opportunistic injection attempt, and discuss why you'd want different severities for each.
- Author a Shuffle playbook (Phase 4+) that auto-blocks a source IP at a mock firewall API after N rule-31164 hits in M seconds, and reason about the false-positive risk of that automation.
- Re-run with a 10-second delay between requests. Does rule 31164 still fire? What does that tell you about rate-based vs. signature-based detection?

## Auto-grading rubric (from `SCN-010-web-attack-login-vic-web.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `medium` (±1 step → `low`/`high` credited) | 15 |
| Confidence = `high` (±1 step credited) | 5 |
| Required observables present (source IP, vic-web) | 15 |
| Summary contains SQLi-related and scanner/automation-related keywords | 10 |
| Enrichment (asked, not graded — no `required: true` entry) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they avoid asserting an outcome the alerts don't state?** This is the single best discriminator of understanding. A student who escalates to critical "because the DB was dumped" — or dismisses it "because nothing happened" — invented a result the 31103/31152 alerts never reported. Strong students explicitly say "attack confirmed, success unknown from this evidence."
- **Severity reasoning.** Medium vs. low is defensible; *why* they chose it matters more than which. Listen for "real attack, no evidence of impact" (good) vs. "it's bad because SQL injection is bad" (shallow).
- **Summary quality.** Could a Tier 2 lead read it in 20 seconds and know: what, who, whether it worked, what to do? The "whether it worked" clause is the one students drop.
- **Did they think about exposure?** Strong students flag that an internet-reachable host taking scanner traffic is itself worth a conversation with the asset owner, beyond this one alert.

## MITRE ATT&CK mapping

- **T1190 — Exploit Public-Facing Application.** The core technique: injecting crafted input at an exposed web endpoint to attempt exploitation.
- **T1595.002 — Active Scanning: Vulnerability Scanning.** The volume, payload variety, and `sqlmap` User-Agent indicate automated vulnerability scanning rather than a single hand-crafted attempt.

## Real-world parallel

This is the single most common alert a real Tier 1 web-facing SOC sees: commodity SQL-injection scanners (sqlmap, and the bot frameworks that wrap it) continuously sweep every internet-exposed `/login`, `/admin`, and `/api` endpoint on the internet. The overwhelming majority fail against patched/parameterized apps — which is exactly why the "real attack that failed is still a true positive, dispositioned by *blocking the source*, not by closing the ticket" muscle matters: the day one of these hits an unpatched endpoint, the analyst who has been reflexively closing them as FP misses the breach. The 2021 wave of automated injection scanning that followed public PoCs for several CMS plugins is a representative public example of how fast commodity scanning weaponizes a new SQLi.
