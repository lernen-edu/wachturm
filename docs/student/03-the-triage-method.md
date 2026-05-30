# 03 — The Triage Method

This is the most important document in the student docs. Re-read it after every five scenarios you complete. The work gets easier in proportion to how thoroughly you internalize this method.

## The four steps

Every alert you triage, in every scenario, in every real SOC job for the rest of your career, follows the same four steps. They are:

1. **Read** the alert.
2. **Investigate** — pivot for evidence, enrich the observables.
3. **Decide** — verdict, severity, confidence.
4. **Document** — case summary and next steps, then close.

That's it. Everything else is technique inside one of those four steps. New analysts often want a more complicated method, looking for the "real" trick experienced analysts know. There isn't one. The trick is doing each step properly, in order, without skipping.

The most common failure mode in Tier 1 is **collapsing two steps into one**. The student reads the alert and decides in the same breath — "looks like brute force, FP, close." They didn't investigate. They didn't enrich. They made a hand-wave decision and then went looking for evidence to support it. That's not triage; it's pattern-matching followed by motivated reasoning. It feels efficient. It is not.

Do the four steps. In order. Always.

## Step 1: Read

You're going to read three things, in this order: the alert title, the alert body, and the asset context.

**The alert title** tells you what kind of detection fired. "SSH multiple authentication failures." "Suspicious PowerShell encoded command." "Outbound connection to TOR exit node." This is the *category* of activity Wazuh thinks it saw. It is not yet the answer.

**The alert body** tells you the specifics. What host? Which user? What source IP? What time? What was the exact log line that triggered the rule? Read these specifics. *Do not skim.* The specifics are where the answer hides.

**The asset context** is what kind of host this is and what role it plays. An SSH brute force against your internet-facing jumpbox is interesting. An SSH brute force against an internal-only test box that nobody uses is also interesting but in a different way. Same alert, different verdict, because the asset is different.

Two questions to answer before leaving Step 1:

1. What is this alert claiming happened?
2. To whom did it claim to happen?

If you cannot answer both clearly, do not proceed to Step 2. Re-read.

## Step 2: Investigate

Investigation has two halves: **pivot** and **enrich**.

### Pivot

A single alert is one snapshot of one moment of one host. The story is rarely in the snapshot. To get to the story, you pivot to other data sources.

Useful pivots, roughly in order of how often you'll use them:

- **Pivot in time.** Look at the same host's activity in the 60 minutes before and after the alert. What else fired? What was the host doing? A brute force followed by silence is different from a brute force followed by a successful login is different from a brute force followed by another brute force from the same source.
- **Pivot by source.** Look at every alert that mentions the source IP (or source host, or source user). Has this IP triggered other detections? Is it triggering them right now? Is it making the same noise against five other hosts?
- **Pivot by target.** Look at the target host's alerts in the recent past. Has it been hit before by similar activity? Did this same alert fire yesterday, last week?
- **Pivot to raw logs.** When the alert summary isn't enough, go to the raw log entries that triggered it. The detection rule abstracts; the raw log doesn't lie.

The pivot you choose depends on the alert. With practice you will know which pivot to try first. As a beginner: start with "pivot in time on the affected host." It's the most-often-correct first pivot.

### Enrich

Enrichment is asking external sources what they know about the observables in your alert. An observable is anything specific enough to look up: an IP address, a domain, a file hash, a user account, a URL.

In Wachturm you enrich through **Cortex**. Cortex runs analyzers against observables and returns structured information: reputation scores, prior reports, geographic data, WHOIS records.

The habit to build: **every alert with at least one external observable gets at least one enrichment lookup.** Even when you're confident the answer is "false positive, ignore." Even when the enrichment returns nothing useful. The habit is what counts. The day you stop enriching by default is the day you miss a real compromise because you "knew" what the answer was.

A nuance for Wachturm specifically: most of the IP addresses in scenarios are RFC1918 private addresses (10.x.x.x). External enrichment services like AbuseIPDB won't have anything on them — they're internal. Run the analyzer anyway. The act of running it, seeing the empty result, and noting it in your case is the discipline. In a real environment with public IPs, the same habit will save you.

## Step 3: Decide

You owe three decisions: **verdict**, **severity**, and **confidence**.

### Verdict

Three values:

- **True positive (TP)** — there is genuine malicious or unauthorized activity. Escalation or response warranted.
- **False positive (FP)** — the detection fired on legitimate activity. The rule did its job; the activity wasn't malicious.
- **Benign (or benign-suspicious)** — the activity isn't malicious *and* the rule didn't really fire incorrectly; the activity was just unusual enough to surface. A user logging in at 3 AM from their hotel during legitimate travel is benign-suspicious.

The distinction between FP and benign is subtle but it matters. An FP suggests the rule may need tuning. A benign-suspicious case suggests no rule change is needed; the activity is just notable.

Most real Tier 1 ticket queues are roughly 70% FP, 25% benign, 5% TP. Internalize this. **Your default expectation should be "this is probably an FP."** A TP is the unusual case, not the normal case. New analysts arrive expecting every alert to be an APT; experienced analysts know that almost nothing is, and the discipline is to confirm the boring answer carefully before settling on it.

### Severity

Four values, usually: `low`, `medium`, `high`, `critical`.

Severity reflects **impact and urgency together**. A confirmed compromise of a workstation is high. A confirmed compromise of a domain controller is critical. Mass failed logins against a non-existent user are low. A successful login after a brute force is high.

A useful test: **how soon does someone need to act?** If the answer is "now," it's high or critical. If the answer is "today," it's medium. If the answer is "this week or never," it's low. If the answer is "never, just closing it for the record," set it low and close.

### Confidence

Three values: `low`, `medium`, `high`.

Confidence is **how sure you are of your verdict**. Not the same as severity. You can be high-confidence about a low-severity FP ("the weekly Nessus scan ran, this is what it always looks like, this is fine"). You can be low-confidence about a high-severity TP ("there's *something* here, my best read is compromise, but I'm not sure and I want Tier 2 eyes").

Be honest about confidence. A low-confidence high-severity TP that you flag for escalation is much better than a high-confidence verdict you don't really believe.

## Step 4: Document

The case is your output. Two parts: **the summary** and **next steps**.

### The summary

Your case summary is what a Tier 2 lead reads when they pick up your escalation, or what your team lead reads at end-of-shift review, or what an auditor reads when reconstructing what happened. It needs to communicate the situation in under 30 seconds of reading.

The next document in this series, **[Writing Case Summaries](04-writing-case-summaries.md)**, is entirely about this. Read it. Most analysts undervalue this skill; the ones who don't get promoted faster.

### Next steps

Even for FPs, document next steps. For an FP, the next step might be "no action, close." For a benign-suspicious case, the next step might be "verified with user, no action." For a TP, next steps are real: contain the host, reset credentials, escalate to Tier 2, preserve evidence, notify the affected team.

A few common next-step categories:

- `close_no_action` — FP or confirmed benign
- `monitor` — close, but flag for awareness if it repeats
- `escalate_t2` — Tier 2 investigation needed
- `contain_host` — network-isolate or shut down the asset
- `reset_credentials` — invalidate the compromised account
- `notify_user` — confirm the activity with the affected user before deciding
- `preserve_evidence` — forensic preservation before any cleanup

For real cases, the next step often is the analyst's most consequential decision. Choose carefully.

## What good triage looks like

A well-triaged case has these properties:

- The verdict is right.
- The severity reflects real impact and urgency.
- The summary stands alone — someone reading only the summary, without seeing the alert, can understand what happened.
- The observables that mattered are attached to the case.
- At least one observable was enriched, even if the enrichment returned nothing.
- Next steps are specific and actionable.
- The total case touched what needed to be touched and nothing else.

The last property matters more than new analysts expect. Spending 90 minutes on a case that any experienced analyst would close in 8 minutes is not thoroughness; it's a queue full of un-triaged alerts piling up behind you while you spelunk. Confident, fast closure of routine cases is the *core* Tier 1 skill. The interesting cases get the time they need; the routine cases get the time they deserve. Learn to tell which is which.

## What bad triage looks like

Bad triage usually has one of these tells:

- The verdict was set before any investigation happened.
- The summary contains conclusions but no evidence.
- No observables enriched.
- The severity doesn't match the verdict (high-severity FP, low-severity TP — both nearly always wrong).
- Next steps say "monitor" without specifying for what.
- The investigation didn't pivot — the analyst stayed inside the original Wazuh alert and concluded from there.

If you find yourself producing any of these tells, slow down. The fix is almost always returning to Step 1 and re-reading the alert without your initial assumption.

## How to practice

Every scenario in Wachturm is an opportunity to practice the four steps. Be explicit with yourself:

> "Step 1 — read. The alert is X. It happened to Y."
> "Step 2 — investigate. I'll pivot in time on Y. Then I'll enrich the source IP in Cortex."
> "Step 3 — decide. Based on what I found, my verdict is Z, severity W, confidence V."
> "Step 4 — document. My summary is..."

This feels mechanical for the first dozen scenarios. After fifty, you won't think about the steps explicitly anymore. Your hands will go to the right places without your conscious mind narrating. That's when you're a Tier 1 analyst.
