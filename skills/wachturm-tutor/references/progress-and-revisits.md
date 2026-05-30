# Progress & Revisits — Reference

This is how the tutor *remembers* a student across sessions. Everything else in this skill reads the **live** stack (docker / `/api/state` / IRIS / Cortex) to know what's happening *right now*; this file is the **durable** half — what happened *before*, what the student struggled with, and what's due to be revisited.

## The boundary (read this first)

You stay **read-only on the student's work** — their IRIS case, the lab, Wazuh, Cortex. You never write to those; you only read them to verify.

But you **own your own notes.** The tutor keeps a small gradebook at **`~/.wachturm/tutor/`** — your record of how the student is doing across sessions. You read it at the start of a session and write to it on specific events. This is *your* notebook about the student, the way a human tutor keeps notes between lessons; it is never the student's case work. Writing here does **not** violate the read-only rule, because what you write is yours, not theirs.

Create it if missing (`mkdir -p ~/.wachturm/tutor`). If you can't write there — locked-down host, or an advisory-tier agent with no file tools — degrade gracefully: run from live state + conversation only, and tell the student once that you won't remember this session next time. Never fabricate continuity you don't have.

## The three files

### `~/.wachturm/tutor/state.json` — where the student is + per-scenario struggle

One small JSON object. Read at session start; rewrite on events (a scenario starts, a hint or relent happens, a case closes).

```json
{
  "student": "optional name/handle if they gave one",
  "current_scenario": "SCN-002",
  "last_seen": "2026-05-30",
  "scenarios": {
    "SCN-001": { "attempts": 1, "hints_used": 0, "relented": false, "passed": true,  "last_verdict": "true_positive" },
    "SCN-002": { "attempts": 2, "hints_used": 1, "relented": true,  "passed": false, "last_verdict": null }
  }
}
```

- `attempts` — how many times they've worked this scenario.
- `hints_used` — cumulative *tutor* hints you've given on it (your coaching ladder; distinct from `make hint`'s scored hints).
- `relented` — did you ever give the answer? This is the durable "the system should know when you relented" signal.
- `passed` / `last_verdict` — the most recent `make score` outcome and the verdict they set.

### `~/.wachturm/tutor/log.md` — append-only history

One line per closed-and-scored case, appended at debrief. Only ever append — never rewrite or reorder.

```
2026-05-30 | SCN-001 | true_positive  | clean run, caught the post-auth pivot unprompted
2026-05-30 | SCN-002 | false_positive | needed a hint to check for the *absence* of a success
```

You read this to pick cold-revisit targets and to ground your greeting ("last time you…").

### `~/.wachturm/tutor/notebook/SCN-NNN.md` — the debrief note

After a scenario closes, you run the five-question debrief (below) as a conversation, then write a short note here capturing it — the durable record of what the student got and what they missed, which you resurface later.

## Session bootstrap (do this in SKILL.md Step A, alongside the live-state check)

1. `mkdir -p ~/.wachturm/tutor` (no-op if it exists).
2. Read `state.json`. Missing or empty → a new student; start fresh (you'll create it on the first event).
3. Read the tail of `log.md` to see what they've done and how it went.
4. Combine with the **live** `/api/state` so your greeting reflects where they *actually* are: *"Welcome back. Last session you closed SCN-002 but needed a hint on the FP discriminator, and SCN-001 is due for a cold revisit. Want to revisit that, or push on?"*

A returning student should feel *known*; a new one gets the normal cold open.

## Writing on events (never wait for a session-end flush — a triage session can die mid-investigation)

- **Scenario starts** (you see a new `active_scenario`): set `current_scenario`; ensure a `scenarios[id]` entry exists; bump `attempts` on a re-attempt.
- **You hint or relent**: bump `hints_used`; on relent set `relented: true`. Write *immediately* — the whole point is that it survives the session.
- **Case closes + scored**: set `passed` / `last_verdict`; append a `log.md` line; run the debrief and write the notebook note.

## The five-question debrief (at scenario close)

Conduct it as a conversation, then record it. **Gate the next scenario on it** — don't let the student bounce to a fresh case without consolidating this one. If their answers are shallow, push for substance before you record.

1. What did this scenario teach — name the technique or the discriminator.
2. What in the alert/evidence was the tell?
3. What was your verdict, and the one piece of evidence that decided it?
4. What would have made you call it the *other* way — and did you check for it?
5. What will you do differently when you next hit a scenario like this?

Question 4 is the most important: it captures the disconfirming check (Common Pitfall #2) and the wrong paths they took — exactly the past struggle worth resurfacing.

## Cold revisits (the payoff)

Spaced retrieval is what makes learning stick. Periodically — every few scenarios, or at the start of a fresh session when `log.md` shows work from a while ago — pull a **prior** scenario and have the student redo one sub-task **blind**: no notes, no re-reading the case, no tools open at first.

1. Read `log.md`. Prefer a scenario from a few sessions back, especially one the notes flag as shaky (a hint, a relent, a thin debrief).
2. Pick one concrete sub-task — *"SCN-002 again: from memory, what was the single thing that made it a false positive and not a compromise?"*
3. Do **not** name the verdict or the discriminator; recognizing it cold is the whole point.
4. Debrief the revisit and append a `log.md` line noting how it went.

The original scenario teaches; the cold revisit is what hardens it. A student who can re-derive SCN-002's FP discriminator three sessions later actually owns it.
