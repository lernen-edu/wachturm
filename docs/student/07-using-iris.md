# 07 — Using DFIR-IRIS

DFIR-IRIS is your case management platform — sometimes called a SIRP (Security Incident Response Platform). It is the system of record for everything you investigate. If Wazuh tells you *what fired*, IRIS records *what you decided about it*. **Every scenario in Wachturm ends with a closed IRIS case, and `make score` grades that case.**

Access: **`https://127.0.0.1:9000`** (IRIS uses HTTPS even locally; the self-signed-certificate browser warning is expected — proceed past it). Log in with the IRIS administrator credentials printed by **`make first-run-creds`**. IRIS forces a password change on first login; set anything you like — the lab is loopback-only.

## The IRIS mental model

IRIS organizes work as **cases**. A case represents one investigation. A case has a title and metadata, **IOCs/observables** (IPs, hashes, usernames, hostnames, URLs), a **summary** (your write-up — this is what gets read and graded), **tags** (how Wachturm records your verdict/severity/confidence — see below), and a **state** (open … closed).

The Wachturm Wazuh→IRIS integration creates the case **for you** the moment a qualifying alert fires: it opens pre-populated with the alert's details and the auto-extracted observables (for SCN-001 the attacker source IP is already attached as an IOC). Your job is to investigate, record your conclusion, and close it.

> A scenario run can create **several** cases (one per qualifying alert burst). `make score` grades **the case you closed most recently** — that is your "this is my answer" signal. Triage one case to completion and close *exactly that one*. Leave the ambient/noise cases open.

## How Wachturm records a verdict in IRIS — the tag convention

DFIR-IRIS does not have built-in "verdict" or "confidence" fields. Wachturm therefore uses a simple, explicit **tag convention** on the case. Add these three tags (Case → the tags field; type each, press Enter):

| Tag | Allowed values |
|---|---|
| `verdict:<value>` | `true_positive` · `false_positive` · `benign` |
| `severity:<value>` | `low` · `medium` · `high` · `critical` |
| `confidence:<value>` | `low` · `medium` · `high` |

Example for a confirmed brute-force compromise: `verdict:true_positive`, `severity:high`, `confidence:high`.

Tags are **case-insensitive** and tolerant of stray spaces (`Verdict: True_Positive` scores the same as `verdict:true_positive`) — but the *value* must be one of the allowed words. Severity and confidence are graded with a ±1-step tolerance: if the answer key says `high` and you put `medium`, you still get the points; `low` (two steps off) you do not. The verdict has **no** tolerance — it is 50% of the score, so think before you tag.

## The IRIS workflow, mapped to the triage method

| Triage step | What you do in IRIS |
|---|---|
| 1 — Read | Open the case the integration created. Note the auto-attached observables. (Most reading happens in Wazuh; you start the case file here.) |
| 2 — Investigate | Pivot in Wazuh. Enrich the key observable in Cortex (see [08 — Using Cortex](08-using-cortex.md)) and bring the result back. Add any required observable that wasn't auto-extracted as an IOC. |
| 3 — Decide | Set the `verdict:` / `severity:` / `confidence:` tags. |
| 4 — Document | Write your assessment in the case **Summary** (the case Description). Close the case. |

## Observables vs. IOCs in IRIS

- **Observable** — anything specific enough to look up: an IP, a hash, a domain, a username. May or may not be malicious.
- **IOC** — an observable *confirmed or suspected* malicious. A SOC's IOC database is institutional memory; promoting something to IOC says "future cases should treat this as bad." Make that claim deliberately.

The scoring engine checks that the scenario's **required observables are present on the case as IOCs** (matched by value). The integration pre-attaches the triggering one; if the answer key expects others (e.g. the targeted host and account) and they're not on the case, add them yourself during triage — Add IOC, set value and type.

## Writing the case Summary (this is graded)

`make score` reads the case **Description / Summary** field and checks it contains the substance of the conclusion (keyword groups from the answer key — e.g. for a true-positive compromise it looks for the *mechanism*, like "brute force," **and** the *outcome*, like "successful login / compromise"). The keywords follow your verdict: a **false-positive or benign** summary states the *opposite* outcome — "no successful authentication," "authorized activity," "false positive" — so match your summary to what actually happened, and never force the true-positive wording onto a case that wasn't one. Write a real two-or-three-sentence analyst conclusion, in your words: what happened, what the evidence was, what you recommend. Don't keyword-stuff — a genuine summary naturally contains the right language. See [Writing Case Summaries](04-writing-case-summaries.md).

If you enriched an observable in Cortex, **record that finding here** ("Source IP enriched via DShield — no prior attack reports; consistent with an internal host"). That sentence proves you did the enrichment and feeds the summary the grader reads.

## Closing a case correctly

1. The three tags are set (`verdict:` / `severity:` / `confidence:`).
2. The required observables are attached as IOCs.
3. Your assessment is written in the case Summary.
4. **Close the case** (Case → Close). Closing sets the case state to *Closed* and is what makes `make score` consider it your submission.

Then, on the host:

```
make score SCN=SCN-001
```

You get a per-component breakdown (verdict / severity / confidence / observables / summary / enrichment), the total, and the answer-key reasoning so you can see exactly where you gained or lost points. Re-open, fix, re-close, and re-run as many times as you like — the most recently closed case is always the one graded.

## What IRIS isn't

IRIS is not your detection engine — it doesn't *find* anything. Detection is Wazuh; enrichment is Cortex; the decision is in your head; IRIS is where all of that becomes a permanent, gradeable record. New analysts sometimes try to "investigate inside IRIS" — it isn't built for that. Search in Wazuh, enrich in Cortex, record in IRIS.

## Common IRIS pitfalls

- **Closing the wrong case.** A scenario can spawn several cases. `make score` grades the most recently *closed* one — close the case you actually triaged, not an ambient noise case.
- **Skipping the tags.** No `verdict:` tag = zero on 50% of the score, no matter how good your summary is.
- **Treating the Summary as optional.** If you didn't write it, you didn't triage — and the keyword component scores zero.
- **Forgetting required observables.** The Wazuh→IRIS integration is best-effort. If the answer key expects an observable and it isn't on the case as an IOC, add it.
- **Confusing the alert with the case.** A Wazuh alert is a detection event; an IRIS case is a unit of investigative work. One case can encompass many related alerts.
