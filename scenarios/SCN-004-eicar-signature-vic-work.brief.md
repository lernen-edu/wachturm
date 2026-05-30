# SCN-004 — Known-malware signature detected on vic-work

**Difficulty:** Beginner
**Estimated time:** 10–20 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-004 triggered at 11:26 UTC. Wazuh raised a
**malware-signature** alert: the workstation **vic-work** repeatedly
requested a file matching a known-malware signature from an internal
web host. The request was logged several times in a short window.

The alert is **low severity**. Day shift flagged it for triage and
disposition.

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-004` — each hint costs 5
points from your auto-score.
