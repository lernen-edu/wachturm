# SCN-003 — Instructor Companion

## Scenario summary

A legitimate user (`bobsmith`) mistypes their SSH password six times
from their own workstation — Caps Lock, or a stale saved credential
after a rotation — pauses, gets it right, logs in, and does nothing
else. It is the deliberate subtle foil to SCN-001: same superficial
shape (failures then a success) but **low volume (no 5763), no
compromise correlation (no 40112), a legitimate account, and zero
post-auth activity**. Correct verdict: **benign** — ordinary human
error, no incident. This is the hardest of the three beginner SSH
scenarios because it is the one most likely to be over-escalated.

> **Same lab signal as SCN-001 and SCN-002 — by design.** All three
> present source `10.50.10.250` → `vic-jump` (SCN-001/002 target the
> `admin` account, SCN-003 targets `bobsmith`). Near-identical at the
> network level; the verdict comes from volume, correlation, account
> legitimacy, and behavior — never from the address. Say this in
> debrief if students played the triad and thought it was a bug; it is
> the entire lesson.

## Learning objectives

- Internalize that **"failed logins followed by a success" is not
  automatically a compromise** — the canonical SCN-001 pattern has a
  benign twin, and conflating them is the most common Tier-1 error.
- Use volume and rule escalation as discriminators: 6 failures (no
  5763, no 40112) is categorically different from a brute-force burst.
- Read Wazuh's *own correlation* as a signal: if 40112 didn't fire,
  Wazuh's logic does not consider this a compromise — weigh that.
- Calibrate confidence: a benign verdict resting on the *absence* of
  malice warrants `medium`, not `high`.

## Required prior knowledge

- Ideally SCN-001 first — this scenario only teaches its lesson as a
  contrast to the brute-force-into-compromise pattern.
- Wazuh Alerts view; reading `srcip`/`dstuser`/source counts.
- True positive vs. false positive vs. benign distinctions.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 15 minutes (run as the third of the SCN-001/2/3 set)

## Full solution walkthrough

### Step 1 — Read

The brief: several failed `bobsmith` SSH auths on `vic-jump` from one
source, then one success from that same source; no non-auth alerts. The
phrase "followed by one successful authentication" is the deliberate
SCN-001 echo — bait for verdict-jumping.

### Step 2 — Investigate

- **Count the failures.** ~6 failures from the source that also produced
  the success — not the sustained, high-rate volume of SCN-001.
- **Check rule escalation.** Rule 5760 fired for the mistypes; **5763
  (brute force) did NOT fire** — the volume is below threshold. **40112
  (multiple failures followed by a success) did NOT fire** — Wazuh's own
  compromise-correlation does not consider this a compromise.
- **Check the account and post-auth behavior.** `bobsmith` is a known
  legitimate user. The Wazuh archives / `vic-jump` logs show **no
  commands after the successful login** — nothing ran.
- Extract observables (IP `10.50.10.250`, host `vic-jump`, user
  `bobsmith`); attempt Cortex enrichment on the IP (RFC1918 → empty;
  same teaching point as SCN-001/002).

### Step 3 — Decide

- Verdict: **benign**
- Severity: **low**
- Confidence: **medium**

Benign because: low volume (no 5763), no compromise correlation (no
40112), legitimate account, and no post-auth activity — the signature of
human error (Caps Lock / stale saved credential after a rotation), not
an attack. The opposite verdict (TP) would need volume, a 40112, or
post-auth behavior; all are verifiably absent. Confidence is **medium**,
not high, *on purpose*: the verdict rests substantially on the absence
of malicious follow-on, which is weaker than a positive indicator. A
student who reflexively writes "high" should be challenged.

### Step 4 — Document

Summary: legitimate user `bobsmith` produced six failed SSH auths from
their workstation (`10.50.10.250`), then authenticated successfully,
with no brute-force/compromise correlation and no post-auth activity;
consistent with mistyped credentials. Severity low. Next steps: close
benign, document, optionally advise the user (password manager / check
Caps Lock after rotations). No escalation.

## Common student errors

1. **Pattern-matches SCN-001 and escalates TP.** Sees "failures then
   success," recalls SCN-001, marks true positive, escalates. This is
   THE error this scenario exists to surface.
   *Redirect:* "Put SCN-001's cluster next to this one. What fired there
   — in volume and in correlation rules — that did NOT fire here? What
   is Wazuh's 40112 logic telling you by staying silent?"

2. **Calls it a false positive.** Says FP because "no real attack." But
   no detection rule misfired on legitimate *tooling* here — a real user
   made real auth failures; the rule worked correctly. That is benign,
   not FP. (Contrast SCN-002, which is a true FP: a rule fired on
   sanctioned scanner activity.)
   *Redirect:* "Did a rule fire incorrectly, or did it correctly record
   a human making mistakes? FP and benign are different dispositions —
   which fits?"

3. **High confidence on a benign verdict.** Marks confidence high.
   Benign-from-absence deserves medium; you cannot fully prove a
   negative.
   *Redirect:* "What evidence would make this NOT benign? How hard did
   you look for it, and how does that bound your confidence?"

4. **Closes with no user-facing follow-up.** Verdict right but no
   next-step. Real SOCs often drop the user a note ("looks like you had
   trouble logging in — all good?") which both helps the user and
   surfaces account-takeover cases where the user says "that wasn't me."
   *Redirect:* "If this user later says 'I never failed any logins that
   day,' what would you wish you had done now?"

## Discussion questions

1. SCN-001 and SCN-003 both end in "failed logins then a success." List
   every discriminator you used. Which single one was most decisive?
2. Rule 40112 stayed silent here. How much weight should an analyst put
   on the *absence* of a correlation rule? When is that reasoning
   unsafe?
3. You set confidence to medium. What specific additional evidence would
   move you to high — and is it obtainable at Tier 1?
4. What minimal change to this scenario would flip it to a true
   positive? To a false positive? (Forces them to articulate the
   boundaries.)
5. The same source IP appeared in SCN-001, SCN-002, and SCN-003 with
   three different verdicts. What does that tell you about IP-based
   reasoning as a primary triage signal?

## Stretch challenges

- Re-run with a 7th–12th failure added from the same source. At what
  point does 5763 fire? Does 40112 ever fire on a "user typo" shape?
  Where exactly is the benign/suspicious boundary in this ruleset?
- Write a saved Wazuh query that returns, for any user, failures grouped
  by source IP so a real cluster is immediately distinguishable from
  scattered noise.
- Pair SCN-001 → SCN-002 → SCN-003 as a graded triad and have students
  write the one-sentence rule they would teach a new hire to tell them
  apart.

## Auto-grading rubric (from `SCN-003-ssh-auth-failures-bobsmith.yml`)

| Criterion | Points |
|---|---|
| Verdict = `benign` | 50 |
| Severity = `low` (or within ±1 step) | 15 |
| Confidence = `medium` (or within ±1 step) | 5 |
| Required observables present (src IP, hostname, user) | 15 |
| Summary contains user-error and benign/low-volume keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Hints cost 5 points each from the final score.

## Manual assessment guidance

- **Did they resist the SCN-001 reflex?** The headline thing to assess.
  A student who escalated this TP "to be safe" needs to hear why
  reflexive escalation is itself a failure mode (alert fatigue, eroded
  signal, the boy who cried wolf).
- **Confidence calibration.** Did they reason about *why* medium, or
  just pick one? The reasoning is the skill.
- **Did they consider account takeover and rule it out properly?** The
  strongest students note that "benign user typo" and "attacker with
  valid creds who happened to fumble" can look alike, state what
  additional check (ask the user, check geo/time, check post-auth) would
  separate them — then confirm it is absent here.

## MITRE ATT&CK mapping

**None — this is ordinary user error, not adversary behavior.** As in
SCN-002, note that rule 5760 carries `T1110.001` in its own metadata;
that tag describes the signature the rule matches, not the verdict of
this event. Reinforce: a rule's ATT&CK tag is never, by itself,
evidence of an attack.

## Real-world parallel

The single most common benign authentication ticket in any SOC: a user
fat-fingers their password after a forced rotation, or Caps Lock is on,
or a reconnected VPN replays a cached old credential a few times before
the user notices and fixes it. Every analyst sees dozens of these. The
skill is not detecting it — Wazuh already did — it is *correctly
declining to escalate it* while still ruling out account takeover and
(the mature move) closing the loop with the user so the rare "that
wasn't me" surfaces fast.
