# SCN-015 — New scheduled-task/cron persistence on vic-web

**Difficulty:** Medium
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-015 triggered at 05:30 UTC. Wazuh raised a
**crontab-change** alert (rule 2832, "Crontab entry changed") on the
web host **vic-web**: a new scheduled job was installed for the
`deploy` account.

A new cron entry is a common persistence mechanism. Day shift flagged
it for triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Change-management / CI-CD pipeline records

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-015` — each hint costs 5
points from your auto-score.
