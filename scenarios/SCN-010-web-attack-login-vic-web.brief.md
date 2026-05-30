# SCN-010 — Web-application attack pattern against /login — vic-web

**Difficulty:** Beginner
**Estimated time:** 15–25 minutes
**Source of alert:** SIEM

## Ticket

Alert cluster #2026-0518-010 triggered at 14:07 UTC. Wazuh raised
web-attack rules on the public web host **vic-web** — rule 31103
("SQL injection attempt"), escalating to 31152 ("Multiple SQL injection
attempts from same source") — for a rapid series of HTTP requests to
`/login` from a single source IP. Each request carries
SQL-injection-style content in the query string, and the requests share
a `sqlmap`-style User-Agent.

No other alert groups are associated with this cluster. Triage and
disposition.

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

If stuck, request hints via `make hint SCN=SCN-010` — each hint costs 5
points from your auto-score.
