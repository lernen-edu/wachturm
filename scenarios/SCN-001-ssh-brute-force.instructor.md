# SCN-001 — Instructor Companion

## Scenario summary

An external attacker brute-forces SSH credentials against the jump host `vic-jump` and eventually succeeds against the `admin` account, then performs basic post-authentication reconnaissance. This is a true positive credential compromise; the correct verdict is escalation with credential reset.

## Learning objectives

- Recognize SSH brute force signatures in a SIEM (Wazuh rule 5760 "sshd: authentication failed", escalating to 5763 "sshd: brute force").
- Understand the significance of a successful login *following* a brute-force pattern (Wazuh rule 40112 "multiple authentication failures followed by a success") — the key pivot point.
- Pivot from a SIEM alert to source-IP context using observable enrichment.
- Distinguish authorized scanner traffic from real brute force by examining source-IP behavior.
- Formulate appropriate next steps for credential compromise (contain, reset, escalate).

## Required prior knowledge

- Basic understanding of SSH authentication and password-based access.
- Familiarity with the Wazuh dashboard's Alerts view.
- Concept of true positive vs. false positive in alert triage.
- Awareness that "lots of failed logins followed by a success" is the canonical brute-force-into-compromise signature.

## Estimated timing

- **Student work:** 15–25 minutes
- **Class debrief:** 15 minutes

## Full solution walkthrough

A competent Tier 1 analyst would:

1. **Spot the alert cluster.** In the Wazuh dashboard's Alerts view, the student sees a burst of rule 5760 ("sshd: authentication failed") and PAM rule 5503 ("PAM: User login failed"), escalating to rule 5763 ("sshd: brute force trying to get access to the system"). All reference source IP `10.50.10.250`, target `vic-jump`, account `admin`. (The `admin` account exists, so failures decode to 5760 — *not* 5710, which is specifically for non-existent users; a common point of confusion.)

2. **Note the timeline.** The failures cluster in a ~60-second window. Aggressive brute force, not slow-and-low.

3. **Find the successful login.** Rule 40112 ("Multiple authentication failures followed by a success") fires within the same window — Wazuh's built-in brute-force-into-compromise correlation, level 12. *This is the moment the scenario transitions from "noisy brute force, probably blocked" to "credential compromise, definitely escalate."* Students who miss this step will conclude FP-low-severity.

4. **Open the auto-created case in IRIS.** Observables should include source IP `10.50.10.250`, hostname `vic-jump`, user `admin`. Confirm these are populated.

5. **Identify the source as hostile, and enrich it.** Wachturm runs on a flat lab network — the attacker is *not* on a separate subnet. The analyst identifies `10.50.10.250` as hostile the way a real SOC does: it is not in the known-good asset inventory (legitimate victims are `.10/.20/.30/.40`; the benign noise generator is `.5`). Reinforce that "hostile vs. trusted" is an inventory/threat-intel judgment, not a subnet-partition shortcut. Then run the AbuseIPDB analyzer in Cortex. (The IP is RFC1918-private, so enrichment returns empty — itself a teaching moment about why context-aware sources matter. The student should still attempt it.)

6. **Pivot to post-auth activity.** Wazuh's archives or the agent logs on `vic-jump` show that after the successful login, commands `whoami`, `id`, `uname -a`, `sudo -l` were run. This is reconnaissance — the attacker is now establishing situational awareness.

7. **Set the case verdict.**
   - Verdict: `true positive`
   - Severity: `high`
   - Confidence: `high`
   - Summary should mention: brute force pattern, successful authentication, post-auth reconnaissance, attacker now has interactive access.

8. **Define next steps.** Minimum: contain `vic-jump` (network isolate or shut down), reset the `admin` password, escalate to Tier 2 for investigation of what else the attacker may have touched.

9. **Close the case** with the summary and next steps populated.

## Common student errors

1. **Fixates on the failures, misses the success.** The student spends 10 minutes admiring the brute force pattern, concludes "noisy but blocked," and closes as FP-low. They didn't scroll past the failures to find rule 40112.
   *Redirect:* "Walk me through the last alert in the cluster. What does it say happened?"

2. **Misses post-auth recon, undersells severity.** The student catches the successful login but rates severity as `medium` because "they just logged in, didn't do anything bad yet." They didn't pivot to the command history.
   *Redirect:* "After the login succeeded, what commands did the attacker run? What do those commands tell you about intent?"

3. **Forgets observable enrichment.** Student closes the case without running any Cortex analyzers. The auto-grader penalizes this, but the deeper issue is they didn't form the habit of "always enrich before concluding."
   *Redirect:* "If this IP showed up again next week, what would you want to know about it? How would you find that out today?"

4. **Skips next-steps entirely or writes "monitor."** "Monitor" is what you do when something is uncertain. Confirmed credential compromise demands action — credentials reset, host contained, scope-of-impact assessment escalated.
   *Redirect:* "If the attacker is logged in right now with those credentials, what should happen in the next 15 minutes?"

5. **Marks verdict as FP because they recognize the attack tool.** Some students see `hydra` in the user-agent or process tree and conclude "this is just a tool, it's pen-testing, FP." This conflates *attack tooling* with *authorized testing*. Without a documented engagement letter, brute force against your jumpbox is an attack regardless of what tool ran it.
   *Redirect:* "Where would you go to confirm this is authorized testing? What does the absence of that documentation tell you?"

## Discussion questions

1. The successful login came from the same IP as the failures. How would your verdict change if the failures came from one IP and the success came from a different IP — say, an internal one?
2. The compromised account was `admin`. How would your severity and next-steps change if it was a regular user, like `bobsmith`?
3. The attacker ran `whoami`, `id`, and `sudo -l` after logging in. What do those three commands tell you, in order, about the attacker's experience level?
4. Wazuh fired rule 40112 ("multiple authentication failures followed by a success") cleanly here. How could an attacker structure a brute force to *avoid* triggering that correlation?
5. What detection or response capability does this scenario reveal as a gap? (Hint: where was MFA? where was rate limiting? where was account lockout?)

## Stretch challenges

- Modify Wazuh's `local_rules.xml` to detect this pattern with one tuned rule rather than relying on the chained 5760 → 5763 → 40112 sequence.
- Author a Shuffle playbook (Phase 4+) that auto-isolates the source IP via a mock firewall API when rule 40112 fires.
- Re-run SCN-001 with a 30-second delay between every failed login attempt. Does Wazuh still detect it? If not, what threshold needs adjustment?

## Auto-grading rubric (from `SCN-001-ssh-brute-force.yml`)

| Criterion | Points |
|---|---|
| Verdict = `true_positive` | 50 |
| Severity = `high` (or within ±1 step) | 15 |
| Confidence = `high` (or within ±1 step) | 5 |
| Required observables present (src IP, hostname, user) | 15 |
| Summary contains brute-force-related and successful-login-related keywords | 10 |
| Enrichment (asked, not graded — answer key has no `required: true`) | 5 |

Hints cost 5 points each from the final score.

## Manual assessment guidance

The auto-scorer can't measure these, but the instructor should:

- **Quality of summary writing.** A good summary is a paragraph that a Tier 2 lead could read in 20 seconds and understand the situation. Look for: timeline, mechanism, evidence, conclusion.
- **Investigation approach.** Did the student methodically work through the alerts, or did they jump to a conclusion and reverse-engineer evidence? Watch for the "pivot at the right moment" — when they noticed rule 40112 and shifted from "brute force" to "compromise."
- **Did they check for lateral movement?** Strong students will, after concluding TP, also check whether the compromised credentials were used elsewhere. The scenario doesn't include lateral movement, but the *instinct* to check is what's being assessed.
- **Communication tone.** A real Tier 1 ticket needs to communicate urgency without panic. Did the student's summary read like a professional ticket or like a stress-typed Slack message?

## MITRE ATT&CK mapping

- **T1110.001 — Brute Force: Password Guessing.** The initial activity. Attacker iterates through a password list against a known username.
- **T1078 — Valid Accounts.** Once successful, the attacker is operating with valid credentials. This is the technique that makes the activity dangerous — they now look like a legitimate user.

## Real-world parallel

This scenario reflects a pattern seen in countless internet-exposed-jumpbox compromises: a misconfigured firewall exposes SSH on a non-standard port, internet scanners find it (Shodan, Censys, Internet-wide scan campaigns), and credential brute force eventually succeeds against an account with a weak or default password. Two well-documented public incidents in this shape are the 2017 Dyn DNS / Mirai botnet credential-spray campaigns, and the ongoing China-attributed credential-spray campaigns documented by Microsoft Threat Intelligence as "Storm-0558"-adjacent activity. Students should leave this scenario understanding that **any externally-reachable SSH service without MFA, rate limiting, and account lockout is a foreseeable compromise**.
