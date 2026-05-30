# SCN-021 — Repeated authentication failures, then success and a new persistence artifact — vic-jump

**Difficulty:** Advanced
**Estimated time:** 30–45 minutes
**Source of alert:** SIEM (handoff)

## Ticket

Night-shift handoff. Starting ~02:00 UTC, Wazuh logged a sustained run
of failed SSH authentications against **vic-jump** for the account
`mwong` from a single source. The failures continued for a while, then
**stopped** — followed by a successful authentication for `mwong` from
that same source, and then a short session of activity.

Night shift triaged the early failures as "noise, monitoring" and moved
on; the activity continued after they did. Pick this up, correlate the
full picture, and close it.

## What you have access to

- Wazuh dashboard (Alerts view; the raw archives / session detail across the time window)
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

If stuck, request hints via `make hint SCN=SCN-021` — each hint costs 5
points from your auto-score.
