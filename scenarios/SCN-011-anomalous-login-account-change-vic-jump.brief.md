# SCN-011 — Login from an unrecognized source then account and file changes — vic-jump

**Difficulty:** Medium
**Estimated time:** 20–30 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-011 triggered at 13:08 UTC. Wazuh logged a **successful
SSH authentication** on the jump host **vic-jump** for the user `jdoe`
from a single source IP. There was **no** preceding failed-login burst.
Shortly after the login, the session ran a series of commands and a
file under `/home/jdoe` was touched.

Day shift does not have a change record or a travel notice on file for
`jdoe` at this time, and the source IP is not one they immediately
recognize. Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives / session detail)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Asset inventory and change/travel records (to check the source and the account)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-011` — each hint costs 5
points from your auto-score.
