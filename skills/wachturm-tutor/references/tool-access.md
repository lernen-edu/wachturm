# Tool Access — Reference

How to query the Wachturm stack so you know what the student is actually doing. This is the technical underpinning of "context-aware" tutoring.

## A reminder about scope

**Everything in this document is read-only.** You query state to verify the student's claims and to know what to ask next. You do not POST, PUT, PATCH, or DELETE against any of these APIs. You do not run `make` commands that change scenario state. You do not edit the student's IRIS case directly. (The *one* thing you write is your own tutor notes at `~/.wachturm/tutor/` — your across-session gradebook, never the student's work; see `references/progress-and-revisits.md`.)

This isn't a technical limitation — your shell access could do those things. It's a *role* constraint. The student is in their own window doing the work. You are in your window having a conversation. Crossing that line collapses the pedagogical model.

When you find yourself thinking "I could just go fix this for them," redirect to: "What question can I ask that gets them to fix it themselves?"

## Discovery order

Always run these in order at session start, then re-run as needed during the session:

1. Stack health
2. Active scenario state
3. Student's IRIS case
4. Cortex job history
5. Scenario answer key (from the YAML, never revealed to student)

## 1. Stack health

Confirm Wachturm is running before assuming anything else.

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E '(wazuh|iris|cortex|wachturm)'
```

Expected: at minimum `wazuh-manager`, `wazuh-indexer`, `wazuh-dashboard`, `wachturm-portal` show as healthy. If `casemgmt` profile is up, you'll also see `iris-app`, `iris-db`, `iris-rabbitmq`, `iris-nginx`, `cortex`, `cortex-es`.

If the output is empty or missing critical services, you're in setup-coaching mode. Don't assume anything else about scenario state.

## 2. Active scenario state

Query the portal's state endpoint:

```bash
curl -sf http://127.0.0.1:8000/api/state
```

Expected JSON shape (Phase 3 will produce this; in earlier phases the file may be missing or sparse):

```json
{
  "active_scenario": "SCN-001",
  "scenario_status": "running",
  "scenario_started_at": "2026-05-16T14:22:00Z",
  "scenario_completed_at": null,
  "expected_case_id": null,
  "last_score": null
}
```

`scenario_status` values:
- `"not_started"` — no scenario active
- `"running"` — scenario is executing now
- `"completed"` — scenario finished, student should be triaging
- `"closed"` — student closed the IRIS case
- `"scored"` — `make score` was run

If the endpoint returns 404 or empty, the state-writing infrastructure isn't online — fall back to asking the student what they're working on.

## 3. Student's IRIS case

This is the most important query: what has the student *actually done* in their case so far?

### Get an IRIS API token

For dev/local Wachturm the simplest path is to ask the student to paste their IRIS API key once, or to read it from a config the runner writes. Document this in the session: *"To check your work, I need to peek at your IRIS case. Paste your API token from IRIS → Account → API."*

Alternatively, if Wachturm's runner writes a `~/.wachturm/iris.token` file (Phase 3 should), read from there.

### List cases (most recent first)

```bash
TOKEN="<token>"
curl -sk \
  -H "Authorization: Bearer $TOKEN" \
  "https://127.0.0.1:9000/manage/cases/list"
```

Find the case matching the active scenario (the runner tags cases with the scenario ID where possible).

### Get a specific case

DFIR-IRIS v2.4.20 has **no** working `/case?cid=` summary endpoint (it
returns HTTP 500). Use the two endpoints that do work — the same ones
the repo's `tools/triage_as_key.py` and this skill's
`scripts/gather-state.sh` use:

```bash
# case list — carries case_description (the "Summary" the student
# writes), case_tags (the verdict:/severity:/confidence: convention),
# and state_name/state_id (9 = Closed):
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://127.0.0.1:9000/manage/cases/list"

# a case's IOCs / observables:
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://127.0.0.1:9000/case/ioc/list?cid=<case-id>"
```

`gather-state.sh` already returns the case list under `iris.cases`; for
most checks you do not need a second call.

### What to check from the case data

- **Observables** — query `/case/ioc/list?cid=<id>`; are the ones the scenario expects present? Compare to `expected_observables` in the scenario YAML. *Do not tell the student which are missing; ask them what observables they think matter.*
- **Summary** — the student's written assessment is the case's `case_description` (the IRIS "Summary" field), visible in `/manage/cases/list`. Check length, presence of a verdict keyword, specific timestamps/entities.
- **Verdict / severity / confidence** — IRIS v2.4.20 has no native fields; Wachturm uses the **case-tag convention**, so read `case_tags` from `/manage/cases/list` (`verdict:<...>,severity:<...>,confidence:<...>`, case-insensitive). Match against what the student tells you they decided. Closed = `state_id` 9 / `state_name` "Closed".
- **Timeline notes** — are there any? An empty timeline plus a closed case is a tell that the student rushed.

### IRIS API documentation

If commands above don't work for the current IRIS version, the canonical reference is:

```
https://docs.dfir-iris.org/operations/api/
```

The IRIS API has evolved across v2.x. If you hit auth or schema errors, that doc is the source of truth.

## 4. Cortex job history

Find out which analyzers the student actually ran.

```bash
CORTEX_KEY="<api-key>"
curl -s \
  -H "Authorization: Bearer $CORTEX_KEY" \
  "http://127.0.0.1:9001/api/job?range=0-50"
```

Returns a list of recent analyzer jobs. Filter for those run in the last hour against observables matching the current scenario.

What to check:
- Did the student run any analyzers at all? (Common Pitfall #5 — closing without enriching)
- Did they run an analyzer against the source IP?
- Did the analyzer return useful data, or empty (RFC1918 expected-empty case)?

Cortex's API key is read from the runner's config in Phase 2+, typically `~/.wachturm/cortex.token` or similar.

## 5. Scenario answer key — your private reference

The scenario YAML at `scenarios/SCN-NNN-<slug>.yml` contains the answer key. **You read this; you do not share it.**

```bash
cat scenarios/SCN-001-ssh-brute-force.yml
```

Pay attention to:
- `answer_key.verdict` — TP / FP / BN
- `answer_key.severity` — low / medium / high / critical
- `answer_key.confidence` — low / medium / high
- `answer_key.required_observables` — what the student should have in their case
- `answer_key.summary_keywords` — phrases that should appear in their summary
- `answer_key.next_steps` — what their recommendations should include
- `answer_key.reasoning` — the canonical explanation (for your private use)

You also have access to the **instructor companion document** at `scenarios/SCN-NNN-<slug>.instructor.md`. This document is full of spoilers — it lists the common student errors, discussion questions, and complete solution walkthrough. **Read it before tutoring a scenario — and, exactly like the answer key, you read it but never share any of it with the student**, including the common-errors list (those "errors" name the very observables and pivots the student has to find for themselves). It is your shared vocabulary with the human instructor. When you suspect the student is hitting "common error #2 from the instructor doc," that's your *private* cue for a specific Socratic **question** — never a recital of what the doc says.

## 6. Wazuh alert data (advanced)

You usually do not need to query Wazuh directly — the student does that through the dashboard. But occasionally you'll want to verify what alerts actually exist for the current scenario, especially when the student says "there are no alerts" and you want to confirm whether that's true.

The cleanest path for Tier-1 tutoring purposes is to read `alerts.json` directly:

```bash
docker exec wazuh-manager tail -n 200 /var/ossec/logs/alerts/alerts.json
```

Each line is a JSON alert record. Filter for the recent timeframe and the affected host. If you need the Wazuh REST API instead, see `https://documentation.wazuh.com/current/user-manual/api/reference.html`.

## State you should keep in mind across the session

The skill's natural memory is the conversation context. Track these across turns:

- **What mode you're in** (setup, intro, scenario, review, reflection).
- **What scenario is active.**
- **What the student has already told you they did** — and what your queries verified.
- **What hints you've already given** — don't repeat them, and escalate if you're about to give the same hint a third time.
- **Where the student is in the four steps.** A student who's clearly in Step 2 should not be answering Step 3 questions yet.
- **Time-in-scenario** — if the student has been on a single beginner scenario for 45+ minutes, you've gone too easy or too hard on them; intervene.

## Failure modes for these queries

You will encounter these. Handle gracefully.

| Symptom | Probable cause | Response |
|---|---|---|
| `docker ps` returns nothing | Docker not running | "It looks like Docker isn't running on your machine. Can you start it and let me know when you're back?" |
| `/api/state` returns 404 | Phase 1 hasn't fully wired the state file yet | Fall back: "Let me ask — what scenario are you on?" |
| IRIS API returns 401 | Token expired or missing | "I can't peek at your case without a fresh token. Paste your IRIS API key, or we'll work without my checking — I'll trust what you tell me but I'll ask more verification questions." |
| Cortex returns no jobs | Cortex not deployed (Phase 2+ only) | Skip enrichment-verification questions; the student is on Phase 1 only. |
| Scenario `completed`/`closed` but **no matching case** in `/manage/cases/list`, and/or `lab_integrity: fail`, `expected_case_id: null` | The detection pipeline failed — the scenario ran but no case was generated (e.g. Wazuh `analysisd` crashed, alert never reached IRIS). **This is an environment failure, not student inaction.** | Switch to **Lab-failure triage** (SKILL.md Step B). Say plainly: *"The scenario ran but the lab didn't generate a case for you — that's an environment problem, not anything you did."* Recovery: re-run `make scenario SCN=...`; if it recurs, `make doctor`, then stack restart / `RESET_YES=1 make reset` + `make up-casemgmt`. **Do not** ask Socratic "what did you miss / what observables did you add" questions about absent work. |
| Scenario YAML not found | Student running outside the wachturm repo, or wrong path | Ask the student to confirm their working directory. The skill needs the repo root in scope. |

In every failure case, surface the limitation honestly and adapt: *"I can't verify your enrichment from here; I'll trust what you tell me, but walk me through what the analyzer showed."*

## A note on privacy and security

The student's IRIS case may contain information they'd consider personal (their reasoning, mistakes, work in progress). Treat their case data the way a careful tutor would treat a student's draft essay — discreet, focused on the work, not gossipy. Don't quote their summary back to them unless you're directly critiquing it. Don't volunteer "I saw you didn't run an enrichment" with a tone — ask them, give them the chance to self-report first.
