# SCENARIO_SCHEMA.md — Scenario YAML Specification

Scenarios are the heart of Wachturm. This document is the locked schema. Changes require a versioned migration of all existing scenarios.

**Schema version:** `1.0`

## 1. The three required artifacts

Every scenario consists of three files in `scenarios/`:

| File | Purpose | Audience | License |
|---|---|---|---|
| `SCN-NNN-<slug>.yml` | Machine-readable spec the runner executes | Runner / CI | CC BY-SA 4.0 |
| `SCN-NNN-<slug>.brief.md` | Student-facing ticket — what they see when they pick up the scenario | Student | CC BY-SA 4.0 |
| `SCN-NNN-<slug>.instructor.md` | Solution walkthrough, common errors, discussion questions, assessment guidance | Instructor | CC BY-SA 4.0 |

**A scenario without all three files is not mergeable.** CI enforces this.

The format for each is below. The skill at `skills/scenario-author/SKILL.md` walks an author through creating all three together.

## 2. File location and naming

Scenarios live in `scenarios/` at the repo root. Filename convention:

```
SCN-<3-digit-id>-<kebab-case-slug>.yml          # the spec
SCN-<3-digit-id>-<kebab-case-slug>.brief.md     # student-facing ticket
SCN-<3-digit-id>-<kebab-case-slug>.instructor.md # instructor companion
```

Example trio:
```
scenarios/SCN-001-ssh-brute-force.yml
scenarios/SCN-001-ssh-brute-force.brief.md
scenarios/SCN-001-ssh-brute-force.instructor.md
```

The YAML is the spec the runner consumes. The brief is what the student reads before they begin. The instructor doc is what the teacher consults during/after the exercise.

## 2. Top-level fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | `"1.0"` for now |
| `id` | string | yes | Format: `SCN-NNN`. Unique. |
| `name` | string | yes | Human-readable title |
| `description` | string | yes | 1–3 sentence summary |
| `author` | string | yes | Attribution (CC BY-SA requires it) |
| `created` | date | yes | ISO 8601 |
| `difficulty` | enum | yes | `easy`, `medium`, `hard` |
| `category` | enum | yes | See §3 |
| `expected_verdict` | enum | yes | `true_positive`, `false_positive`, `benign` |
| `mitre` | list[string] | conditional | Required if `expected_verdict == true_positive`. Format: `Txxxx` or `Txxxx.yyy` |
| `duration_minutes` | int | yes | Approx wall-clock to run |
| `requires` | list[string] | no | Extra tools the attacker container needs |
| `tags` | list[string] | no | Free-form |
| `setup` | object | no | One-time setup actions (e.g., plant a file) |
| `steps` | list[object] | yes | The actions to execute. See §4 |
| `expected_alerts` | list[object] | yes | What Wazuh should produce. See §5 |
| `expected_observables` | list[object] | no | IoCs that should appear in IRIS |
| `hints` | list[string] | no | Progressive hints for stuck students |
| `answer_key` | object | yes | The correct triage outcome. See §6 |
| `scoring_weights` | object | no | Override default rubric weights |

## 3. Categories

Use one of:

- `initial_access`
- `execution`
- `persistence`
- `privilege_escalation`
- `defense_evasion`
- `credential_access`
- `discovery`
- `lateral_movement`
- `collection`
- `command_and_control`
- `exfiltration`
- `impact`
- `benign_admin` — for FP and benign scenarios involving legitimate admin work
- `benign_user` — for FP and benign scenarios involving legitimate user behavior
- `misconfigured_tool` — FPs caused by security tools or scanners

## 4. Steps

A step describes a single action by a named actor. The runner executes them in order, with optional `delay_seconds` between them.

```yaml
steps:
  - actor: atk-kali
    description: "Initial port scan from attacker"
    command: "nmap -sS -p 22,80,443 10.50.10.10"
    delay_seconds: 0
  - actor: atk-kali
    description: "Begin brute force against SSH"
    command: "hydra -l admin -P /opt/wordlists/rockyou-1k.txt ssh://10.50.10.10 -t 4"
    delay_seconds: 5
    timeout_seconds: 60
  - actor: vic-jump
    description: "Attacker reuses cracked credentials"
    command: "echo 'simulated post-auth recon'"
    via: "ssh"
    from: atk-kali
    as_user: admin
    delay_seconds: 10
```

**Step fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `actor` | string | yes | Container name from the inventory |
| `description` | string | yes | Shown in `make scenario` output |
| `command` | string | yes | Shell command to run inside `actor` |
| `via` | enum | no | `direct` (default), `ssh`, `rce_sim` |
| `from` | string | conditional | Required when `via != direct` |
| `as_user` | string | no | Username to run as (default: container default) |
| `delay_seconds` | int | no | Pause before this step (default: 0) |
| `timeout_seconds` | int | no | Kill the step after N seconds (default: 30) |
| `expect_failure` | bool | no | If true, a non-zero exit is the success condition |

## 5. Expected alerts

What Wazuh should produce when the scenario runs cleanly. Used for sanity checking the lab is wired up — *not* used to grade the student.

```yaml
expected_alerts:
  - rule_id: 5710
    description: "Attempt to login using non-existent user"
    minimum_count: 5
    timeframe_seconds: 120
  - rule_id: 5712
    description: "SSHD brute force"
    minimum_count: 1
    timeframe_seconds: 120
  - rule_id: 5715
    description: "SSHD successful login after multiple failures"
    minimum_count: 1
    timeframe_seconds: 180
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `rule_id` | int | yes | Wazuh rule ID |
| `description` | string | no | For human reading only |
| `minimum_count` | int | no | Default 1 |
| `timeframe_seconds` | int | no | Default 300 |

If a scenario completes but `expected_alerts` doesn't materialize within the timeframe, the runner emits a `LAB_INTEGRITY_FAIL` (not a student-facing error).

## 6. Answer key

This is what the student should conclude. The scoring engine compares the student's IRIS case to this.

```yaml
answer_key:
  verdict: true_positive
  severity: high             # low | medium | high | critical
  confidence: high           # low | medium | high
  required_observables:
    - type: ip
      value: "10.50.20.10"
      role: source
    - type: hostname
      value: "vic-jump"
      role: target
    - type: user
      value: "admin"
      role: compromised
  required_enrichment:
    - observable_type: ip
      analyzer: AbuseIPDB
      required: false        # ask but don't grade
  summary_keywords:           # heuristic: at least one of each group should appear
    - any_of: ["brute force", "brute-force", "password spray"]
    - any_of: ["successful login", "authenticated", "compromise"]
  next_steps:
    - contain_host
    - reset_credentials
    - escalate_t2
  reasoning: >
    Multiple failed SSH login attempts from a single source IP followed by a
    successful authentication is a classic indicator of credential compromise.
    The attacker is likely now operating with valid credentials.
```

**Verdict scoring:**
- Correct verdict: 50% of base score.
- Correct severity (within ±1 step): 15%.
- Correct confidence (within ±1 step): 5%.
- All required observables present in the case: 15%.
- At least one `summary_keywords any_of` group matched: 10%.
- Required enrichments performed (when `required: true`): 5%.

Weights are configurable in `scoring_weights`.

## 7. Hints

Hints are revealed on demand by the student via `make hint SCN=SCN-001`. Each hint costs scoring points (configurable, default 5%).

```yaml
hints:
  - "Look at the source IP for the failed login attempts. Is the same IP responsible for the successful login?"
  - "What happens to the alert rate from this source IP over time?"
  - "Check the user account that succeeded. Has it logged in from this IP before?"
```

## 8. Setup actions

Some scenarios need a one-time pre-condition (a file planted on a victim, a user created, a backup snapshot referenced). Define these in `setup:`.

```yaml
setup:
  - actor: vic-work
    command: "useradd -m -s /bin/bash bobsmith && echo 'bobsmith:CorrectHorse42' | chpasswd"
    description: "Create the target user"
  - actor: vic-work
    command: "echo 'this is a fake sensitive document' > /home/bobsmith/Documents/financials.txt"
    description: "Plant a fake sensitive file"
```

Setup is idempotent. The runner tracks which scenarios have been set up and skips re-runs unless `--force-setup` is passed.

## 9. Full example

```yaml
schema_version: "1.0"
id: SCN-001
name: "SSH Brute Force into Successful Login"
description: >
  An attacker brute-forces SSH credentials against the jump host and
  eventually succeeds, then performs basic post-auth reconnaissance.
author: "Wachturm Contributors"
created: 2026-05-15
difficulty: easy
category: initial_access
expected_verdict: true_positive
mitre:
  - T1110.001
  - T1078
duration_minutes: 4
tags: [ssh, credential-access, beginner]

setup:
  - actor: vic-jump
    command: "useradd -m -s /bin/bash admin || true; echo 'admin:Sup3rs3cret!' | chpasswd"
    description: "Ensure target user exists"

steps:
  - actor: atk-kali
    description: "Quick port scan"
    command: "nmap -Pn -p 22 10.50.10.30"
    delay_seconds: 0

  - actor: atk-kali
    description: "Brute force SSH (will find creds in the seeded wordlist)"
    command: "hydra -l admin -P /opt/wordlists/wachturm-easy.txt -t 4 -f ssh://10.50.10.30"
    delay_seconds: 10
    timeout_seconds: 120

  - actor: atk-kali
    description: "Post-auth recon over SSH"
    command: "sshpass -p 'Sup3rs3cret!' ssh -o StrictHostKeyChecking=no admin@10.50.10.30 'whoami; id; uname -a; sudo -l 2>/dev/null'"
    delay_seconds: 5
    timeout_seconds: 30

expected_alerts:
  - rule_id: 5710
    minimum_count: 5
    timeframe_seconds: 180
  - rule_id: 5712
    minimum_count: 1
    timeframe_seconds: 180
  - rule_id: 5715
    minimum_count: 1
    timeframe_seconds: 240

expected_observables:
  - type: ip
    value: "10.50.20.10"
  - type: hostname
    value: "vic-jump"
  - type: user
    value: "admin"

hints:
  - "Check the timing and source of the failed login attempts on vic-jump."
  - "Did the eventual successful login come from the same source as the failures?"
  - "Pivot to the post-auth commands — what did the attacker do once in?"

answer_key:
  verdict: true_positive
  severity: high
  confidence: high
  required_observables:
    - type: ip
      value: "10.50.20.10"
      role: source
    - type: hostname
      value: "vic-jump"
      role: target
    - type: user
      value: "admin"
      role: compromised
  summary_keywords:
    - any_of: ["brute force", "brute-force", "password guessing"]
    - any_of: ["successful login", "compromise", "authenticated"]
  next_steps:
    - contain_host
    - reset_credentials
    - escalate_t2
  reasoning: >
    A sustained burst of failed SSH login attempts from a single source IP
    followed by a successful authentication for the same account is a textbook
    credential brute-force compromise. The subsequent recon (whoami, sudo -l)
    indicates the attacker is establishing situational awareness.
```

## 10. Validation

The Pydantic models in `runner/src/wachturm/scenario.py` are the canonical implementation of this YAML schema. If this doc and the Pydantic models disagree, the Pydantic models win (and this doc gets a PR).

CI runs `wachturm scenario validate scenarios/*.yml` on every push, and also checks that each `.yml` has a matching `.brief.md` and `.instructor.md`.

## 11. Student brief format (`.brief.md`)

The brief is what the student reads when they pick up the scenario. It must read like a real SOC ticket — not a textbook problem. Use one of these openers:

- **SIEM auto-ticket:** "Alert ID #20XXX-N triggered at HH:MM. Source: Wazuh rule N. Triage and disposition."
- **User-reported:** "Helpdesk escalation: user reports unable to access X. Please investigate as IR may be involved."
- **Internal handoff:** "Day-shift handoff: this one came in at 03:14, I started but didn't finish. Pick up and close it."
- **Threat-intel-driven:** "Intel feed indicates active campaign against [sector]. Hunt for IoCs in our environment."

Required sections in the brief:

```markdown
# SCN-NNN — <Scenario Title>

**Difficulty:** Beginner | Medium | Advanced
**Estimated time:** N–M minutes
**Source of alert:** SIEM | User report | Threat intel | Handoff

## Ticket

[Ticket-shaped framing. 2–4 sentences. Conversational. What the analyst sees in their queue.]

## What you have access to

- Wazuh dashboard
- DFIR-IRIS (your case will appear here)
- Cortex (for observable enrichment)
- [Any other tool relevant to this scenario]

## Your task

1. Investigate the alert(s).
2. Determine: true positive, false positive, or benign.
3. Set severity and confidence.
4. Add the relevant observables to your IRIS case.
5. Enrich what's worth enriching.
6. Write a clear, brief case summary.
7. Decide next steps and close the case.

## Hints

If stuck, request hints via `make hint SCN=NNN` — each hint costs 5 points from your auto-score.
```

The brief does **not** include the answer. The instructor doc does.

## 12. Instructor companion format (`.instructor.md`)

The instructor doc is the teacher's reference. It enables real assessment beyond what the auto-scorer can detect.

Required sections:

```markdown
# SCN-NNN — Instructor Companion

## Scenario summary
[1–2 sentence summary of what the scenario simulates and the correct verdict.]

## Learning objectives
- [Specific skill or concept #1]
- [Specific skill or concept #2]
- [Specific skill or concept #3]

## Required prior knowledge
- [Concept the student should already understand]
- [Tool familiarity required]

## Estimated timing
- Student work: N–M minutes
- Class debrief: N minutes

## Full solution walkthrough
[Step-by-step what a competent Tier 1 analyst should do, in order. Include:
- Where they start (which alert in Wazuh)
- What they should pivot to and why
- Which observables matter and why
- Which enrichments are valuable vs. just busy-work
- How to recognize the verdict from the evidence
- How they should write their summary]

## Common student errors
- **[Error pattern]:** [Why they make this error, how to redirect them]
- **[Error pattern]:** [Why they make this error, how to redirect them]
- [Aim for 3–5 entries; this is the highest-value section for instructors]

## Discussion questions
[3–5 questions to drive class discussion after the exercise. Should provoke thinking beyond the immediate verdict — what-ifs, real-world variations, defensive lessons.]

## Stretch challenges
[Optional advanced extensions for students who finish quickly. E.g. "Modify the Wazuh rule to reduce false positives," "Build a Shuffle playbook that auto-handles this pattern."]

## Auto-grading rubric
[Reproduce the scoring breakdown from the YAML answer_key, with point values, so the instructor can talk through it with the student.]

## Manual assessment guidance
[Things the auto-scorer can't measure but the instructor should:
- Quality of case summary writing (clarity, completeness, professional tone)
- Investigation approach (did they jump to conclusions or pivot methodically?)
- Did they go beyond the minimum or stop at the answer?
- Did they appropriately escalate or hold?]

## Reference — MITRE ATT&CK mapping
[Technique IDs from the YAML, with one-sentence explanation of each in context.]

## Real-world parallel
[Optional: a brief mention of a public incident or technique writeup that resembles this scenario, for instructor context.]
```

Instructor docs are licensed CC BY-SA 4.0. Encourage contributors to enrich them — the instructor doc is often where the most teaching value lives.
