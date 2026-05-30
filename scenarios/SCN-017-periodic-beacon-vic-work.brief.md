# SCN-017 — Periodic outbound beaconing pattern — vic-work

**Difficulty:** Medium
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM (NIDS / Suricata)

## Ticket

Alert #2026-0518-017 triggered at 08:30 UTC. Suricata raised a
**beaconing-pattern** alert for the workstation **vic-work**: repeated
outbound connections to a single external endpoint at a regular
interval over TLS. The signature is a behavioural heuristic.

Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view — the Suricata alert and its signature)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment of the destination IP)
- Egress / SaaS allowlist and asset documentation

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-017` — each hint costs 5
points from your auto-score.
