# Ticket: <subject line — like a real SOC ticket>

> **What this is:** the brief is what the student sees when they `make scenario SCN=NNN-...`. It's modeled on a real Tier 1 SOC ticket. Match the tone of a SIEM-generated alert summary, not a textbook problem.
>
> **What goes in it:** the alert that triggered the ticket, the asset(s) involved, the time window, the noise level around it. NOT: hints about the verdict, what the student should do, or what the answer is.
>
> **What does NOT go in it:** anything that gives away the answer. No "this looks like a brute force attempt" — let the student decide. No "the source IP is suspicious" — let them investigate. The brief is the *prompt*, not the answer.

---

**Alert:** <one-line alert title as it appears in Wazuh>

**Detected:** <YYYY-MM-DD HH:MM:SS UTC>

**Asset:** <hostname or container name, e.g., vic-jump>

**Severity:** <low | medium | high — from Wazuh's rule, not what the student should set>

**Summary:**

<2–3 sentences describing what the SIEM saw. Use technical language. Reference rule IDs, specific count thresholds, source/destination if known. Example:

> Wazuh rule 5712 (Authentication failure burst) fired on `vic-jump` at 14:32 UTC. 47 failed SSH login attempts from `10.50.20.10` targeting the `root` account within a 90-second window. Following the burst, one successful authentication was logged.

>

## What you have to work with

- Wazuh alerts queue
- IRIS case auto-created from the alert
- Cortex available for observable enrichment

## What you're being asked to do

Triage this ticket. Open the case in IRIS, investigate, and close it with a verdict (true positive, false positive, or benign) plus a case summary supporting your decision.

Use the four-step triage method: **Read → Investigate → Decide → Document.**

Refer to `docs/student/03-the-triage-method.md` if you want a refresher.

---

> **Time budget:** ~<estimated_minutes from the YAML> minutes. Use `make hint SCN=NNN-...` if you get stuck — each hint costs 5 points from your auto-score.
