# SCN-008 — Internal port scan across the victim subnet

**Difficulty:** Beginner
**Estimated time:** 10–20 minutes
**Source of alert:** SIEM (NIDS / Suricata)

## Ticket

Alert #2026-0518-008 triggered at 06:00 UTC. Suricata raised an
**internal port-scan** alert: a single host on the internal subnet
making repeated connection attempts across multiple ports/hosts.

Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view — the Suricata alert and its signature)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Asset inventory / documented-scanner list

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-008` — each hint costs 5
points from your auto-score.
