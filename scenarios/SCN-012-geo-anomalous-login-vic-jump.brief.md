# SCN-012 — Successful login from an unrecognized geographic source — vic-jump

**Difficulty:** Medium
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-012 triggered at 09:52 UTC. Wazuh logged a **successful
SSH authentication** on the jump host **vic-jump** for the user
`awilson` from a single source IP. There was **no** preceding
failed-login burst. The source geolocates well outside `awilson`'s
usual region; the session then ran a few routine commands.

SIEM enrichment auto-correlated `awilson` to a possible **travel /
helpdesk note** for this period. The correlation is informational only
and has **not** been validated against the observed activity.

Triage and disposition: compromised account, authorized activity, or
something else?

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives / session detail)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Helpdesk / travel records and the asset inventory (to verify the note)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-012` — each hint costs 5
points from your auto-score.
