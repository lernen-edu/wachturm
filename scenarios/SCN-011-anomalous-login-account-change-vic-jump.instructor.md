# SCN-011 — Instructor Companion

## Scenario summary

An attacker with stolen valid credentials logs into `vic-jump` as `jdoe` from an unrecognized source — a single clean SSH success, no brute force — then runs recon, reads a sensitive file, and plants an SSH `authorized_keys` entry for persistence. Correct verdict: **true positive** — account takeover. This is the deliberate TP counterpart to SCN-034 (same 5715 success alert, opposite verdict).

## Learning objectives

- Internalize that **a single clean login can be a compromise** — you cannot rely on a brute-force burst to flag every account takeover.
- Make the verdict from the *source* (inventory/records) and the *post-auth behaviour*, not from auth-failure volume.
- Recognize SSH `authorized_keys` injection as persistence and a force-multiplier (credential reset alone won't evict the attacker).
- Practice the SCN-034 contrast: identical alert, opposite disposition, decided by context + behaviour.

## Required prior knowledge

- SSH auth and what a Wazuh "authentication success" (5715) alert means.
- The four-step method; pivoting from an alert into session/post-auth activity.
- Basic persistence concept (`~/.ssh/authorized_keys`).

## Estimated timing

- **Student work:** 20–30 minutes
- **Class debrief:** 15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Read the alert.** Wazuh 5715 ("sshd: authentication success") on `vic-jump`, user `jdoe`, source `10.50.10.250`. Note immediately: **no** 5760 burst, **no** 5763/40112 — this did *not* come in via brute force.

2. **Resist "no brute force ⇒ benign."** The absence of a failure burst means entry was via *valid credentials*. That raises the question, it doesn't answer it. (This is the SCN-003/SCN-034 muscle used in the opposite direction.)

3. **Check the source and the account against records.** `10.50.10.250` is not in the known-good inventory (legit victims `.10/.20/.30/.40`; benign noise `.5`). There is no change record or travel notice for `jdoe`. Compare deliberately with SCN-034, where a verified break-glass record existed — here it does not.

4. **Pivot into the session — this is the decisive step.** The post-auth activity: `whoami; id; uname -a`, `cat /home/jdoe/financials.txt`, then `echo ... >> ~/.ssh/authorized_keys`. Recon + sensitive-data access + persistence. That is an intruder, not jdoe doing their job.

5. **Open the IRIS case.** Observables: source IP `10.50.10.250`, hostname `vic-jump`, user `jdoe` (compromised). Confirm/add.

6. **Enrich the source.** AbuseIPDB in Cortex on `10.50.10.250` — RFC1918, empty (the SCN-001/010/034 teaching point: habit, not a dead end).

7. **Set the verdict.**
   - Verdict: `true positive` — account takeover via stolen credentials.
   - Severity: `high` — active compromise with persistence and data access.
   - Confidence: `high` — the post-auth behaviour is unambiguous.
   - Summary: clean login from an unrecognized source, no change/travel record, recon + sensitive-file read + planted authorized_keys = takeover.

8. **Next steps.** Contain `vic-jump`, reset `jdoe`'s credentials, **remove the planted key** (credential reset alone does not evict an attacker who owns an authorized_keys entry), escalate to Tier 2 to scope further access.

## Common student errors

1. **"No failed logins ⇒ not an attack" → closes benign/FP.** The single biggest trap; mirrors SCN-003/SCN-034 reasoning misapplied.
   *Redirect:* "How did the attacker get in if there was no brute force? What does a *successful* login with no failures tell you about how they got the password?"

2. **Stops at the login, never pivots to post-auth.** Sees 5715, sees "no brute force," dispositions without reading what the session did.
   *Redirect:* "Walk me through every command that ran in that session, in order. Does that look like jdoe's normal work?"

3. **Misses the persistence; recommends only 'reset password'.** Catches the takeover but the authorized_keys line slips by.
   *Redirect:* "If you reset jdoe's password right now, can the attacker still get back in? Look again at what they wrote to disk."

4. **Treats this like SCN-034 and waves it through as authorized.** Pattern-matches "single clean privileged-ish login" to the break-glass scenario without checking that the *records and behaviour* differ.
   *Redirect:* "In SCN-034 you verified a break-glass record. Do that here. What did you find — and what did the session do that a break-glass admin wouldn't?"

5. **Severity `medium` ("they only read one file").** Undervalues persistence + confirmed data access.
   *Redirect:* "They left themselves a key and read a file named 'financials'. Is the incident over, or just starting?"

## Discussion questions

1. SCN-034 and SCN-011 produce nearly the same alert. List every signal that distinguishes them, ranked by how decisive it is.
2. Entry was via valid stolen credentials. Where would those realistically have come from, and which of those origins would *this* alert ever show you?
3. The attacker planted an SSH key. What detection would have caught *that* specifically, and why didn't this alert depend on it?
4. How would your triage change if `financials.txt` had not been read but the key was still planted? Same verdict? Same severity?
5. What single inventory/process improvement would have made this a 30-second triage instead of a pivot-heavy one?

## Stretch challenges

- Propose a Wazuh FIM (syscheck) configuration that would alert on `~/.ssh/authorized_keys` modification, and discuss its false-positive profile across a real fleet.
- Write the Tier-2 escalation: what scoping questions does Tier 2 need answered, and which can Tier 1 pre-answer from this data?

## Auto-grading rubric (from `SCN-011-anomalous-login-account-change-vic-jump.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `high` (±1 step → `medium`/`critical` credited) | 15 |
| Confidence = `high` (±1 step credited) | 5 |
| Required observables present (source IP, vic-jump, jdoe) | 15 |
| Summary contains takeover/compromise and persistence/post-auth keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Each revealed hint costs 5 points from the final score.

## Manual assessment guidance

The auto-scorer can't measure these; the instructor should:

- **Did they pivot, or pattern-match?** The whole scenario rewards pivoting into the session. A student who wrote "true positive" because "unknown IP = bad" got lucky, not skilled — probe whether they actually read the post-auth commands.
- **Did they catch the persistence?** "Reset the password" without "remove the key" is an incomplete, real-world-dangerous response. This is the highest-signal discriminator of understanding.
- **The SCN-034 comparison.** Strong students explicitly contrast it ("same 5715, but no record and malicious post-auth"). That comparison is the point of pairing the two.
- **Summary quality.** Could Tier 2 act on it in 20 seconds: who, from where, what they did, what persists, what to do?

## MITRE ATT&CK mapping

- **T1078 — Valid Accounts.** Entry via stolen valid credentials, not exploitation/brute force — why there is no failure burst.
- **T1098.004 — Account Manipulation: SSH Authorized Keys.** The planted `authorized_keys` entry; persistence that survives a password reset.
- **T1005 — Data from Local System.** Reading `financials.txt` — confirmed data access, which drives severity.

## Real-world parallel

This is the textbook post-credential-theft intrusion: credentials are phished or bought, the attacker logs in *cleanly* (no brute force to detect), does quick recon, grabs data, and drops an SSH key so they own the box even after the obvious remediation. SOCs that only alert on brute force miss this entire class — which is exactly why the lesson "a single successful login from the wrong place, doing the wrong things, is a compromise" is worth a dedicated scenario, paired with SCN-034 so students feel how thin the line is and how much the *verification* and the *post-auth behaviour* carry the decision.
