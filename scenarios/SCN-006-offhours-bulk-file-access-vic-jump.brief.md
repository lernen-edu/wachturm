# SCN-006 — Off-hours bulk file access by an unfamiliar service account — vic-jump

**Difficulty:** Beginner
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-006 triggered at 03:12 UTC. Wazuh logged a **successful
SSH authentication** on **vic-jump** for the account `svc-backup` from a
single source, well outside business hours. The session then enumerated
a large number of files and created an archive.

Day shift does not recognize `svc-backup` and flagged the bulk file
activity as possible data staging. Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives / session detail)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Asset / change records and the service-account inventory

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-006` — each hint costs 5
points from your auto-score.
