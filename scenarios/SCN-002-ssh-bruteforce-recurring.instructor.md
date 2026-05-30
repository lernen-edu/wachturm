# SCN-002 — Instructor Companion

## Scenario summary

The scheduled weekly authenticated vulnerability scan (Nessus/Qualys/
Tenable-style) runs against the jump host `vic-jump` with a stale scan
credential. Every authentication fails, tripping the exact same Wazuh
signature as SCN-001's brute force (5760 → 5763) — but **no
authentication succeeds, rule 40112 never fires, and no command is run
on the host**. The source and timing match a documented change record.
This is a false positive: authorized, documented security tooling that
is signature-identical to an attack. Correct verdict: close as false
positive, document the scanner, recommend detection tuning.

> **Same lab signal as SCN-001 and SCN-003 — by design.** All three
> beginner SSH scenarios present the *same source IP* (`10.50.10.250`)
> hitting the *same host* (`vic-jump`). This is intentional and is the
> whole point of the triad: the technical signature is identical; only
> the **authorization context** and the **behavioral outcome** differ.
> The discriminator is never "which subnet" or "which IP" — it is
> *did a compromise correlation (40112) fire* and *is the activity
> documented and verified*. Tell students this explicitly in debrief if
> they played the triad back-to-back and assumed it was a lab bug.

## Learning objectives

- Recognize that an authorized vulnerability scanner produces a
  signature **indistinguishable from a brute force** at the rule level
  (5760/5763) — tool tags are not verdicts.
- Use the *absence* of evidence as evidence: no rule 40112, no
  successful auth, no post-auth activity ⇒ nothing was compromised.
- Validate a change-management correlation rather than rubber-stamping
  it: "authorized" is only safe to conclude after verifying nothing
  succeeded.
- Disposition a false positive correctly: close + document + tune, not
  escalate, and not silently ignore.

## Required prior knowledge

- SSH authentication basics and what a credentialed vulnerability scan
  is.
- Wazuh Alerts view; the 5760 → 5763 → 40112 chain (ideally having done
  SCN-001 first — this scenario is its deliberate foil).
- True positive vs. false positive vs. benign distinctions.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 15 minutes (best run immediately after SCN-001)

## Full solution walkthrough

### Step 1 — Read

The brief shows a failed-auth burst on `vic-jump`/`admin` from
`10.50.10.250` escalating to 5763, plus a SIEM enrichment line
correlating the source/window to change record **CHG-2026-0517-VA**
(weekly authenticated vuln scan). The brief explicitly says the
correlation is *informational and not validated* — that phrasing is the
invitation to verify, not to trust.

### Step 2 — Investigate

The decisive move is to **walk the entire alert cluster to its end**, as
in SCN-001 — but here it terminates differently:

- Rule 5760 fires repeatedly, 5763 fires (brute-force pattern). Same as
  SCN-001 so far.
- **Rule 40112 ("multiple authentication failures followed by a
  success") does NOT appear.** There is no successful authentication.
- The Wazuh archives / `vic-jump` agent logs show **no post-auth
  commands** — nothing logged in, so nothing ran.

Then validate the change correlation: the source, the 02:00–02:30 window,
the broad credentialed-probe profile, and the *complete absence of a
successful login* are all consistent with a credentialed scanner whose
scan account is stale. Extract observables (IP `10.50.10.250`, host
`vic-jump`, user `admin`) and attempt Cortex enrichment on the IP (it is
RFC1918 — empty result, same teaching point as SCN-001).

### Step 3 — Decide

- Verdict: **false positive**
- Severity: **low**
- Confidence: **high** (the evidence is unambiguous *once verified*)

It is a false positive because (1) nothing authenticated — 40112 absent,
no post-auth activity, so no compromise occurred; AND (2) the activity
matches a documented, scheduled, authorized scan. Both halves are
required. The opposite verdict (TP) would be supported by a 40112, a
successful auth, or any post-auth command — this scenario rules those out
by their verifiable absence.

### Step 4 — Document

Case summary: authorized weekly vulnerability scan (CHG-2026-0517-VA)
from `10.50.10.250` produced failed-auth noise on `vic-jump`; verified no
successful authentication, no 40112, no post-auth activity; no compromise.
Severity low. Next steps: close as false positive, document the scanner
as an authorized source, and recommend tuning (allowlist the scan
host/window or down-rank the rule for it) to cut recurring alert fatigue.

## Common student errors

1. **Rubber-stamps the change ticket.** Sees "CHG-2026-0517-VA — vuln
   scan," concludes FP in 30 seconds, never checks whether anything
   actually succeeded. This is the *dangerous* error: an authorized scan
   window is exactly when a real attacker would prefer to hide. They got
   the right verdict by luck, not method.
   *Redirect:* "An authorized scan ran in this window. If an attacker had
   also succeeded in this window, would this ticket look any different at
   first glance? How do you prove nothing succeeded?"

2. **Panics on the brute-force pattern, escalates as TP.** Sees 5763 and
   `hydra`-shaped volume, ignores both the documented change and the
   absence of 40112, escalates to Tier 2.
   *Redirect:* "Compare this cluster's ending to SCN-001's. What fired
   there at the end that did not fire here? What does that absence mean?"

3. **Right verdict, wrong severity.** Marks FP but sets severity high
   "because brute force." FP/benign dispositions are low severity; the
   severity reflects impact, and the impact here is zero.
   *Redirect:* "What was the actual impact to vic-jump? What severity
   matches zero impact?"

4. **Closes without recommending tuning.** Verdict correct, but no
   next-step to stop this recurring every week. The same false positive
   will burn the next analyst's time too.
   *Redirect:* "This scan runs every week. What happens to next week's
   shift if you just close this and move on?"

5. **Confuses false positive with benign.** Calls it benign. Benign =
   unusual-but-legitimate activity that *isn't an FP in the rule-fired
   sense*. Here a detection rule fired on legitimate sanctioned tooling —
   that is the definition of a false positive. (Contrast SCN-003, which
   is genuinely benign: a real human error, not authorized tooling.)
   *Redirect:* "Did a rule fire on activity that was legitimate? What do
   we call that specifically?"

## Discussion questions

1. The only difference between this and SCN-001 at the signature level is
   what *didn't* happen. How comfortable are you concluding a verdict
   from absence of evidence? What would make you more or less confident?
2. The change ticket said "authorized vuln scan." What is the minimum you
   must verify before you trust that, and why is trusting it blindly
   dangerous?
3. At 1,000 tickets/day, you cannot deep-verify every scanner FP. How
   would you tune detection so this never pages a human again — without
   going blind to a real attack that hides inside the scan window?
4. How would your verdict change if rule 40112 *had* fired during the
   documented scan window? Walk through it.
5. Where is the line between "false positive" and "benign"? Use SCN-002
   vs. SCN-003 to anchor your answer.

## Stretch challenges

- Write a Wazuh rule (or `local_rules.xml` override) that suppresses
  5760/5763 specifically for the documented scanner host during its
  change window — and argue why time-boxing the suppression matters.
- Design the detection that would still catch a real compromise *during*
  an authorized scan window (hint: 40112 / successful-auth + post-auth
  behavior survives the suppression above).
- Pair with SCN-001 as a back-to-back A/B: same signature, opposite
  verdicts. Have students articulate the single decisive observable.

## Auto-grading rubric (from `SCN-002-ssh-bruteforce-recurring.yml`)

| Criterion | Points |
|---|---|
| Verdict = `false_positive` | 50 |
| Severity = `low` (or within ±1 step) | 15 |
| Confidence = `high` (or within ±1 step) | 5 |
| Required observables present (src IP, hostname, user) | 15 |
| Summary contains authorized-scan and no-compromise keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Hints cost 5 points each from the final score.

## Manual assessment guidance

The auto-scorer can't measure these:

- **Did they verify, or assume?** The single most important thing to
  assess. A student who concluded FP *because the ticket said so* failed
  the scenario even with a perfect auto-score. Look for explicit evidence
  in their summary that they checked for a success / 40112 / post-auth
  activity.
- **Absence-of-evidence reasoning.** Can they articulate *why* "no 40112"
  is strong evidence, not just "I didn't see anything"?
- **Operational maturity.** Did they think past this one ticket to the
  recurring-noise problem? That's the Tier-1-to-Tier-2 mindset.

## MITRE ATT&CK mapping

**None — this is authorized security operations, not adversary
behavior.** Note for debrief: the rules that fired (5760/5763) carry
`T1110.001 — Password Guessing` in *their own* metadata. Students will
see that tag and may cite it as proof of an attack. It is not: a rule's
ATT&CK tag describes the *signature it matches*, not the *verdict of the
event*. Disentangling "the rule is about brute force" from "this event
was a brute force" is a core Tier-1 skill this scenario drills.

## Real-world parallel

This is the single most common false positive in real Tier-1 queues:
the weekly authenticated Nessus/Qualys/Tenable scan hitting the SIEM
with thousands of failed-auth and brute-force-shaped events, every week,
forever. Every SOC that has ever stood up a SIEM has drowned in this for
a sprint or two before tuning it. The lesson students must internalize:
the fix is not "ignore the scanner" (that blinds you to attacks hiding
in the window) and not "escalate every week" (alert fatigue) — it is
*verify, document, and tune precisely*.
