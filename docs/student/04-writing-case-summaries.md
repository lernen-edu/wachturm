# 04 — Writing Case Summaries

The case summary is your output. Not the alert you read; not the analysis you did; the summary you wrote. That paragraph is what gets read by the Tier 2 lead picking up your escalation, the team lead reviewing your shift, the auditor reconstructing the incident six months later, and — if things go badly enough — the lawyer reading discovery.

If your summary is bad, your work is bad, regardless of how good your investigation was. This document is about writing summaries that aren't bad.

## The job a summary has to do

A good case summary answers, in order:

1. **What happened?** (one or two sentences)
2. **What did you do to investigate it?** (one to three sentences)
3. **What did you conclude, and why?** (one or two sentences)
4. **What should happen next?** (one sentence, or a short list)

Length target: **three to six sentences for most cases.** Routine FPs can be shorter. Genuinely complex multi-stage TPs can be longer. If you're writing a page, you're either escalating a real incident (in which case length is appropriate) or you're trying to substitute volume for thinking (which won't work).

## What good summaries do

Three properties:

**They stand alone.** Someone who has never seen the alert can read only the summary and understand the situation. Names, IPs, timestamps, accounts — included. The reader should not have to open the alert to know what you're telling them.

**They state the verdict explicitly.** "This is a true positive" or "False positive — closed" or "Benign, no action." Don't bury the verdict in qualifiers. The reader's first need is to know what you decided.

**They show your reasoning, briefly.** Not your whole investigation; the *evidence that justifies the verdict*. A summary is not a transcript of your work.

## What bad summaries do

Bad summaries fall into recognizable shapes. Avoid all of them.

### The Restatement

> "An alert fired for SSH brute force on vic-jump. After investigating, I determined this is a true positive."

This is the alert title plus a verdict. It contains zero information the reader couldn't have gotten from the alert itself. The investigation is invisible; the reasoning is invisible. Useless.

### The Brain Dump

> "I saw the alert come in around 2pm. I clicked on it and saw multiple failures then opened the host view and looked at the last hour and noticed there was a successful login so I went to Cortex and ran DShield but the IP was private so no result then I added an observable for the user and went back to Wazuh and looked at what commands ran after which were whoami and id and sudo -l so this is a brute force compromise."

This is your raw investigation narrative. Every step you took, in order, no editing. The reader has to do the work of extracting what matters. Don't make them. Write what matters; leave out the rest.

### The Hedge Tower

> "It appears that there may have been an indication of possible unauthorized access activity, though the source could potentially be benign and further investigation might be warranted to determine if escalation could be appropriate."

This summary has decided nothing. Every clause is hedged. The reader cannot act on it because no claim has been made. Hedging is fear of being wrong wearing the costume of professionalism. **Make a call.** If you're genuinely uncertain, set confidence to `low` and *say so directly* — "I'm uncertain; I think it's a TP but I want Tier 2 to confirm." That's better than hedging every word.

### The Tool Tunnel

> "Wazuh rule 5712 fired for vic-jump. Rule 5715 also fired. I ran a Cortex DShield analyzer."

This describes the tools you used, not what happened. The reader doesn't care which Wazuh rule number fired; they care that someone brute-forced an account. Talk about the *event*, then reference the tool only when it adds information.

## A template for routine cases

For most cases, this structure works:

> *[Time/timeframe]*, *[source]* performed *[activity]* against *[target]*. *[Brief description of what investigation showed.]* *[Enrichment results, if relevant.]* *[Verdict and reasoning.]* *[Recommended next steps.]*

Filled in for an FP:

> "Between 03:00 and 03:15 UTC, source IP 10.50.10.50 (the documented monitoring server) performed port scans across the victim subnet, triggering reconnaissance-detection rules. Activity matches the documented weekly Nagios sweep, confirmed via the host's name resolution and consistent scan pattern. Source IP not enriched (internal monitoring asset, not in scope for external reputation). **False positive — closed.** Recommend rule tuning to exclude the monitoring server's IP from this detection."

Filled in for a TP:

> "At 14:22:17 UTC, source IP 10.50.10.250 initiated a sustained SSH brute-force attack against the admin account on vic-jump; the attack succeeded at 14:24:09 UTC. Subsequent reconnaissance commands (whoami, id, uname -a, sudo -l) were executed as admin from the same source. Source IP enrichment via DShield returned no recorded attack history (RFC1918 range, expected). **True positive, high severity — active credential compromise.** Recommend immediate session termination, admin credential reset, vic-jump containment, and Tier 2 escalation for scope-of-impact investigation."

Both are around 60 words. Both stand alone. Both make a verdict explicit. Both end with action.

## On voice and tone

Write like a professional, not like a textbook and not like a colleague at a bar.

**Use active voice.** "The attacker executed `whoami`" beats "the command `whoami` was executed by the attacker."

**Use past tense for what happened, present tense for what you concluded.** "The user logged in successfully" (past) "This is consistent with credential compromise" (present).

**Use specific nouns and verbs.** "Source IP 10.50.10.250" not "the IP." "Brute-forced" not "tried to log in repeatedly." Specificity is professionalism.

**Don't apologize and don't hedge for politeness.** "I couldn't determine X" is fine. "Unfortunately I was unable to fully investigate X due to limited time" is a problem — either you investigated enough to make a call, or you didn't. Make the call or say you can't.

**Don't editorialize.** "This was a really sneaky attack" doesn't belong in a case summary. Save commentary for the post-mortem.

## Common questions

**"What about jargon? Can I assume the reader knows what RFC1918 means?"**

Yes, for an internal SOC audience. Tier 2 leads, team leads, security engineers — they all know the vocabulary. If you're escalating to a non-security stakeholder (legal, HR, an executive), strip the jargon. Different audience, different summary. For Wachturm, write as if your reader is another SOC analyst.

**"How much detail goes in the summary vs. the case timeline notes?"**

The summary states *what matters*. The timeline notes record *everything you did*. A reader who needs the full trail goes to the timeline. A reader who needs the answer reads only the summary. Both audiences are served.

**"What if I'm wrong? What if I write a confident summary for the wrong verdict?"**

You will be. Everyone is, sometimes. The defense isn't hedging; the defense is *appropriate confidence* — when you're sure, say so; when you're unsure, set confidence to `low` and explain what would change your mind. A high-confidence wrong answer is a teachable moment. A wall of hedging is a missed opportunity to learn.

**"My instructor / Tier 2 lead writes summaries totally differently. Whose version is right?"**

Both, probably. Real SOCs have house styles. What's described here is a defensible default — the structure transfers anywhere. Adapt to the conventions of wherever you end up working. The four-question backbone (*what happened, what did you do, what did you conclude, what next*) doesn't change.

## Practicing summary-writing

Wachturm's auto-grader checks summaries heuristically: did you mention the right entities, did you include verdict keywords. It's a coarse check.

The real practice is **rereading your own summaries the next day.** Pick a closed case from yesterday. Read only the summary, pretending you've never seen the case. Can you follow what happened? Would you trust this analyst's conclusion? Would you know what to do next?

If the answer to any of those is "no," you have a target for improvement. Most analysts who do this exercise weekly improve fast.
