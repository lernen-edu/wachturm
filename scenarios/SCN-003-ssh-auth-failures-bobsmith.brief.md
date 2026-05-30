# SCN-003 — SSH authentication failures then success — bobsmith / vic-jump

**Difficulty:** Beginner
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert cluster #2026-0517-003 triggered at 01:02 UTC. Wazuh logged
several failed SSH authentications against the jump host **vic-jump**
for the `bobsmith` account from a single source IP, followed by one
successful authentication for that same account from that same source.

No alerts beyond the authentication rules are associated with this
cluster. Triage and disposition.

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives if you need them)
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

If stuck, request hints via `make hint SCN=SCN-003` — each hint costs 5
points from your auto-score.
