# Student Docs

Welcome to Wachturm. You're going to learn what Tier 1 SOC analysts actually do.

These docs are for you, the learner. Read them in order if you're starting from zero. Skip around if you know what you're after.

> **On Windows?** Set up WSL2 + Docker Desktop first — see **[Running Wachturm on Windows](windows-setup.md)**. After that, everything below works exactly the same.

## Read in this order

1. **[Orientation](01-orientation.md)** — what Wachturm is, what tools are connected to what, where to look for things. *5 minutes.*
2. **[Your First Shift](02-first-shift.md)** — a hand-held walkthrough of your first scenario from start to finish. Do this once, then never again. *30–45 minutes.*
3. **[The Triage Method](03-the-triage-method.md)** — the four-step methodology that every scenario after the first will use. This is the most important document in here. *15 minutes to read, a career to master.*
4. **[Writing Case Summaries](04-writing-case-summaries.md)** — how to write a case summary that a Tier 2 lead can read in 20 seconds. The single most-undervalued skill in Tier 1. *15 minutes.*
5. **[Common Pitfalls](05-common-pitfalls.md)** — what new analysts get wrong, in advance, so you don't have to learn it the hard way. *15 minutes.*

## Reference, look up as needed

6. **[Using Wazuh](06-using-wazuh.md)** — your SIEM. Where alerts are born.
7. **[Using DFIR-IRIS](07-using-iris.md)** — your case management system. Where investigations live and die.
8. **[Using Cortex](08-using-cortex.md)** — your enrichment engine. How to ask "what do we know about this IP/file/domain?"

## When to ask for help

- **Stuck on the environment** (something won't start, can't reach a URL) → check the README at the project root, then ask your instructor.
- **Stuck on a scenario** → use `make hint SCN=SCN-001` (the id of the scenario you're on) to get a progressive hint. Each hint costs 5 points from your auto-score. Use them; that's what they're for.
- **Confused about the methodology** → re-read [The Triage Method](03-the-triage-method.md). It's worth re-reading.
- **Want a tutor that coaches you through scenarios live** → run `make tutor` in a separate terminal. This opens a dedicated coaching window running a coding agent (Claude Code, Codex, Gemini CLI, OpenCode, or Pi) with the Wachturm tutor skill loaded — if you have several installed, `make tutor` lets you pick which one. The tutor is Socratic — it won't give you the answer, but it'll ask the right questions and verify your work as you go. You keep doing your actual SOC work in your browser tabs and other terminals; the tutor is just there in its own window, ready when you want to think out loud.

## A note on what this isn't

Wachturm doesn't teach you offensive security, malware analysis, or threat hunting. Those are different jobs. Wachturm teaches you the daily work of a Tier 1 SOC analyst: read an alert, decide what it is, document your reasoning, escalate or close. Do this well and you have a career.
