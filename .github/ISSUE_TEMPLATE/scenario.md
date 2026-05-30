---
name: Scenario proposal
about: Propose a new scenario for the Wachturm library
title: "[SCN-PROPOSAL] <short scenario name>"
labels: scenario, needs-triage
assignees: ''
---

## Scenario proposal

<!--
Thanks for proposing a scenario! Please complete this template before any
authoring work. The goal is to avoid duplicate effort and keep the library's
distribution balanced.

If you haven't read it yet: skills/scenario-author/SKILL.md is the canonical
workflow for authoring. Read it before opening this issue.
-->

### One-sentence summary

<!-- "An attacker brute-forces SSH against the jumpbox and eventually succeeds." -->

### Real-world parallel

<!--
What real-world incident type does this simulate? Be specific.

Examples:
  - "Simulates an externally-exposed jumpbox compromised via credential brute force, like the pattern seen in countless internet-exposed SSH abuse incidents."
  - "Simulates an authorized weekly vulnerability scan generating noisy alerts the SOC must learn to recognize."

If you can't articulate the real-world parallel in 1-2 sentences, your
scenario is contrived. Please reconsider before opening this issue.
-->

### Difficulty

<!-- One of: beginner / medium / advanced -->

### Verdict type

<!--
One of:
- true_positive (TP)
- false_positive (FP)
- benign (BN)

Real Tier 1 ticket queues are ~70% FP, ~25% benign, ~5% TP. The Wachturm
library is intentionally more TP-heavy (TPs teach more) but FPs are still
the most under-represented contribution type. If your proposal is yet
another TP, double-check that it adds something the library doesn't already
have.
-->

### Category

<!--
One of (from SCENARIO_SCHEMA.md §3):
- initial_access
- execution
- persistence
- privilege_escalation
- defense_evasion
- credential_access
- discovery
- lateral_movement
- collection
- command_and_control
- exfiltration
- impact
- benign_admin
- benign_user
- misconfigured_tool
-->

### MITRE ATT&CK techniques (TPs only)

<!-- e.g., T1110.001, T1078 — at least one technique ID required for TPs -->

### Why this scenario fills a gap

<!--
Check scenarios/_taxonomy.md. Is this slot already in the catalog as OPEN?
If yes, reference the SCN-NNN slot you'd fill.
If no, explain why this scenario should be added to the taxonomy.
-->

### Estimated student difficulty time

<!-- Roughly how long should a competent Tier 1 student spend on this? -->

### Anything else

<!-- Anything else relevant. Skip if not. -->

---

### Before opening this issue

- [ ] I've read `skills/scenario-author/SKILL.md`
- [ ] I've read at least one existing scenario trio for voice/format reference
- [ ] I've checked `scenarios/_taxonomy.md` for duplicates
- [ ] The real-world parallel is clear and grounded in actual incident types
