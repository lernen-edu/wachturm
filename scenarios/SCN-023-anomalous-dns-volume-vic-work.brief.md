# SCN-023 — Anomalous DNS query volume — vic-work

**Difficulty:** Advanced
**Estimated time:** 25–40 minutes
**Source of alert:** SIEM (NIDS / Suricata)

## Ticket

Alert #2026-0518-023 triggered at 22:10 UTC. Suricata raised a
**DNS-anomaly** alert for the workstation **vic-work**: a sustained,
low-rate stream of DNS queries to a single external domain over an
extended window. No single query is remarkable; the alert is on the
aggregate pattern.

Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view — the Suricata alert; the raw archives for the query pattern over time)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment of the destination)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-023` — each hint costs 5
points from your auto-score.
