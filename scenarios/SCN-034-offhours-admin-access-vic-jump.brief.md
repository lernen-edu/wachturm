# SCN-034 — Off-hours administrative remote access — vic-jump

**Difficulty:** Medium
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert #2026-0518-034 triggered at 02:41 UTC. Wazuh logged a **successful
SSH authentication** on the jump host **vic-jump** for the account
`breakglass` from a single source IP, well outside business hours,
followed by a short series of system commands. `breakglass` is not an
account the day-shift recognizes.

SIEM enrichment auto-correlated the account and time window to a
**break-glass / change reference, CHG-2026-0518-EMG**. The correlation
is informational only and has **not** been validated against the
observed activity.

Triage and disposition: intrusion via a privileged account, authorized
emergency access, or something else?

## What you have access to

- Wazuh dashboard (Alerts view, and the raw archives if you need them)
- DFIR-IRIS (your case is auto-created there)
- Cortex (for observable enrichment)
- Your organization's change / break-glass records (to verify CHG-2026-0518-EMG)

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=SCN-034` — each hint costs 5
points from your auto-score.
