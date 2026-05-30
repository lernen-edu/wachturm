# 05 — Common Pitfalls

This document is forewarning. Every new analyst makes some subset of these mistakes. You will make some of them. The goal is to recognize them when you catch yourself in the act, so you can self-correct without needing your instructor to find it for you.

## 1. Deciding before investigating

The single most common Tier 1 mistake. The alert title says "brute force"; the analyst thinks "looks like a brute force, probably FP, close." They didn't pivot. They didn't enrich. They pattern-matched.

The fix: when you notice yourself forming a verdict, **stop** and ask: "what evidence have I actually looked at?" If the honest answer is "the alert title," you have not investigated. Do Step 2. Then decide.

The deeper fix: when you sit down to triage, **explicitly do not form a verdict until Step 3.** Treat Step 1 and Step 2 as evidence-gathering with no opinion attached. Your verdict at the start of Step 1 should be "I don't know yet." Maintaining "I don't know yet" until Step 3 is a discipline. It saves you.

## 2. Hunting for confirmation, not evidence

A close cousin of pitfall #1. Once you form a hypothesis ("this is a TP"), the human brain wants to find evidence supporting it. You go to logs, you see a thing that fits, you stop. You don't ask "what would I see if this were *not* a TP?"

The fix: **ask yourself the disconfirming question.** "If this were actually a benign event, what would I expect to see?" Then look for that. If you don't find disconfirming evidence, your confidence is justified. If you do find it, your hypothesis needs to update.

This is harder than it sounds. The whole industry of cognitive bias research exists because humans are bad at this. The discipline is named *active disconfirmation*, and Tier 1 analysts who practice it close cases with materially better accuracy than those who don't.

## 3. Severity inflation

Every alert feels urgent when you're new. The temptation is to set everything to `high` or `critical` "to be safe."

Don't. Severity inflation in your queue causes the same effect as the boy who cried wolf in your team's queue. If everything you escalate is "high," nothing you escalate is high; your verdicts lose information.

The fix: apply the "how soon does someone need to act?" test from the triage method. *Now* → high or critical. *Today* → medium. *This week or never* → low. Most cases are low or medium. That's correct.

## 4. Verdict-severity mismatch

You concluded TP, you set severity to low. Or you concluded FP, you set severity to high. Both are usually wrong.

A low-severity TP is unusual but possible — for instance, a confirmed compromise of a decommissioned test host that holds no data and is being rebuilt anyway. Most low-severity TPs are actually FPs you haven't accepted yet.

A high-severity FP is almost always wrong. If the activity was legitimate, the severity shouldn't be high; high means impact and urgency, which legitimate activity doesn't have.

The fix: when verdict and severity mismatch, sanity-check yourself. Read the next-steps you wrote. Do those next-steps match the severity? "Recommend immediate Tier 2 escalation" on a low-severity case is a tell.

## 5. Closing without enriching

The temptation is strong, especially for cases that "obviously" look like FPs. You see "weekly Nessus scan," you don't bother running an analyzer, you close.

The cost is hidden but real. The day will come when the IP that "obviously" looks like your scanner is actually someone spoofing your scanner's IP, or scanning during your scanner's window to hide in the noise. The discipline of always-enrich catches this; the habit of selective enrichment doesn't.

The fix: **always run at least one analyzer**, even on cases you're sure are FPs. The 30 seconds it costs you are worth the case it'll catch once in your career.

## 6. Closing without timeline notes

The timeline section of an IRIS case is where you record what you did, in what order, with what result. Many new analysts skip it — they go from "open the case" straight to "write the summary and close."

The cost: when you (or someone else) reopens this case in a month, there's no record of what was checked. If the activity recurs, you can't easily compare "what we saw last time" to "what we see this time." The institutional memory rots.

The fix: write timeline notes as you go. "14:30 — pivoted to host view, confirmed no further activity from source IP" is enough. You don't have to write essays. You just have to leave breadcrumbs.

## 7. Ignoring the post-auth question

In many TP scenarios involving compromised credentials or successful exploitation, the alert that fires is the *moment of compromise.* But the interesting question is often **what happened after.**

A successful brute force is a TP. *What did the attacker do once in?* That changes severity and changes next steps.

A successful phishing click is a TP. *What did the user run? What got downloaded? Where did the session go?* That changes scope.

A SQL injection that worked is a TP. *What was queried? Was data exfiltrated?* That changes everything.

The fix: when you confirm a TP at a specific moment, **always pivot forward in time** for that asset and source. Look at the next 15 minutes, the next hour, the rest of the day. The single alert is one frame; the story is in the sequence.

## 8. Following the alert wherever it leads, indefinitely

The opposite failure of pitfall #1. The analyst goes deep, pivots six layers, ends up in a totally different host's logs, an hour later still hasn't closed the original case.

Real SOC queues are time-constrained. Spending 90 minutes on a case that any experienced analyst would close in 8 minutes means three other cases didn't get triaged this shift. That's the actual cost.

The fix: time-box. If a case feels like it's taking unusually long, ask "what's the simplest reading of this evidence that justifies a verdict?" If you can articulate a simple reading and it's defensible, take it. If you genuinely can't decide, set confidence to `low` and escalate to Tier 2 *with what you have so far*. Escalation is not failure; it's the right call when the answer is genuinely unclear.

The Tier 1 skill is closing the closeable cases confidently and quickly, and escalating the genuinely ambiguous ones early. Not investigating everything to the bottom.

## 9. Trusting tool defaults

Wazuh's severity field, IRIS's auto-assigned tags, Cortex's analyzer verdicts — these are inputs, not answers. New analysts sometimes copy them through without thinking.

A Wazuh "high" rule firing doesn't mean the case is high-severity. The rule severity is what Wazuh thinks; your severity is what *you* think after investigating. Same for analyzer verdicts — VirusTotal saying "0 detections" doesn't mean clean; it means none of the AV engines have seen this hash before, which is exactly what a fresh attacker payload looks like.

The fix: treat tool outputs as *evidence to weigh*, not as conclusions to adopt. If your verdict conflicts with what a tool said, that's interesting and worth a sentence in your summary — not a problem to suppress.

## 10. Not closing the case at all

This sounds obvious but it's surprisingly common: a student investigates thoroughly, writes good timeline notes, then walks away without setting verdict/severity/confidence and clicking the close button. They think the work is done; the case management system thinks the case is open.

A real SOC tracks closed-case-counts per analyst per shift. An "open" case in IRIS is unfinished work. If you don't close it, it doesn't count.

The fix: **the close button is the unit of completion.** Until it's clicked, you haven't finished triaging.

## 11. Asking AI assistants to triage for you

Wachturm is a learning environment. AI tools can write very fluent-sounding case summaries. If you let an AI do the analysis and just paste its output into IRIS, you skipped the learning.

A defensible use: ask an AI to explain a concept you don't understand ("what does sudo -l do?"). An undefensible use: paste the alert in and ask it to make the verdict. The first builds skill; the second erodes it.

If your course has an explicit AI-use policy, follow it. If your instructor's policy requires disclosure, disclose. If it doesn't but you used AI to assist, you owe yourself the honesty of asking "did I learn this, or did I just produce the output?" If the answer is "produced," redo the case without the AI.

## 12. Not asking when stuck

The work culture in real SOCs varies, but in most healthy ones, asking a teammate for a second opinion on a difficult case is normal and expected. Tier 1 analysts who silently struggle for 45 minutes and produce wrong verdicts are not rewarded; analysts who say "I've got something weird, can you take a look?" are.

In Wachturm specifically: use the hint system. `make hint SCN=SCN-001` (use the id of the scenario you're on) will give you a progressive nudge. Each hint costs 5 points from your final score. **Use them.** That cost is much smaller than the cost of producing a wrong verdict and not knowing why.

When you graduate from Wachturm to a real SOC, replace `make hint` with "hey, got a minute? I've got an odd one." Same instinct; different tool.

## 13. Treating every case as a learning opportunity

The opposite of pitfall #12. Some students treat every routine FP as a chance to deeply learn something, spending excessive time on cases that don't reward it.

Most cases in real SOCs are routine. Most cases in Wachturm are too: the library deliberately includes a substantial share of FP/benign cases (though it's still more TP-heavy than a real production queue, where true positives are a small minority — a deliberate trade for teaching value). Confident, quick closure of routine cases is *the* Tier 1 skill. Learning opportunities are the genuinely interesting cases — usually the medium and advanced scenarios, plus the occasional surprising beginner case.

The fix: pace yourself differently for different cases. A clear beginner FP should take 5–10 minutes. A medium-difficulty case with ambiguity might take 20–30 minutes. An advanced multi-stage scenario might take 45–60 minutes. If you're spending 45 minutes on a beginner case, you're probably overthinking it.

---

You will see yourself in some of these. Everyone does. The recognition is the first step toward not repeating them.

Once you can name your own pitfalls in real time — "I'm doing the confirmation hunt again, let me pivot for disconfirming evidence" — you're already a substantially better analyst than someone who can't.
