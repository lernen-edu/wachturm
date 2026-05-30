# SCN-007 — Outbound connection to a threat-flagged IP — vic-work

**Difficulty:** Beginner
**Estimated time:** 10–20 minutes
**Source of alert:** SIEM (NIDS / Suricata)

## Ticket

Alert #2026-0518-007 triggered at 16:18 UTC. Suricata raised a network
alert for an **outbound connection** from the workstation **vic-work**
to an external IP. The signature category and text indicate the
destination is flagged by the NIDS ruleset.

Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view — the Suricata alert and its signature)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment of the destination IP)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-007` — each hint costs 5
points from your auto-score.
