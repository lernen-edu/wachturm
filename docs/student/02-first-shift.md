# 02 — Your First Shift

This is the only walkthrough in the docs. By design. After this, you're expected to use **[The Triage Method](03-the-triage-method.md)** to figure things out on your own. The point of this document is to take you through the full workflow once, slowly, so you know what every screen looks like and what every action accomplishes.

Plan to spend 30–45 minutes here. Don't rush. Don't skip the "stop and look" prompts.

## Before you start

You need:

- Wachturm running with the case-management stack up — `make up-casemgmt` succeeded. (**Not** plain `make up`, which is Wazuh-only: it has no DFIR-IRIS, so there'd be no case to work and `make score` can't run.)
- The portal at `http://localhost:8000` showing **Wazuh** and **DFIR-IRIS** both online.
- About 45 minutes uninterrupted.

We will be running **SCN-001** — an SSH brute force attack against the jumpbox. This is a beginner-level true positive. We'll walk through all four steps of the triage method together.

## Step 0 — Set the stage

From a terminal:

```bash
make scenario SCN=SCN-001
```

You'll see output indicating the runner has begun executing scenario steps. The scenario takes about 4 minutes to play out. During that time, the attacker container is scanning the jumpbox, attempting a brute force, eventually succeeding, and then doing some basic reconnaissance commands as the compromised user.

> **If the very first run reports `LAB_INTEGRITY_FAIL` or "no alerts produced":** the lab was most likely still settling after start-up. Just run `make scenario SCN=SCN-001` again — it's a known cold-start quirk, not a broken lab.

While it runs, open the portal at `http://localhost:8000` in a browser tab. Keep it open. You'll bounce between this tab, a Wazuh tab, and an IRIS tab for the rest of this exercise.

When the runner finishes, you'll see a "scenario complete" message in the terminal. Now the work starts.

## Step 1 — Read

Click **Wazuh** in the portal. You'll land on the Wazuh login page. Log in with `admin` / `SecretPassword` — the fixed lab default. (`make first-run-creds` prints it, the dashboard URL, and every other login any time you need them; the self-signed-certificate warning is expected.)

After logging in, navigate to the **Threat Hunting** or **Security Events** view (different Wazuh versions name it slightly differently). You want the live alert stream.

You should see a burst of alerts that all reference the same source IP and the same target host. They occurred in a tight time window — most within 60 seconds of each other.

> **Stop and look.** Read the alert titles. You'll see several variants of "sshd: authentication failed" and "PAM: User login failed," all from one source IP. Then, near the end of the burst, a different one fires: **"Multiple authentication failures followed by a success"** (Wazuh rule 40112). *That* correlation — failures immediately followed by a success from the same source IP — is the critical alert; note it. (You may also see plain "authentication success" alerts from *other* IPs in the stream; those are unrelated background noise. The decisive signal is the correlation tying the failures to a success from the attacker's IP.)

Click into the burst of alerts to read the details. Note these three things:

1. **The target host.** Probably `vic-jump`.
2. **The source IP.** `10.50.10.250` (this is `atk-kali`'s address, but you don't know that yet — to you it's just a not-in-inventory IP).
3. **The target user.** Probably `admin`.

These three pieces of information are your observables. Write them down on a sticky note if you have to. You'll need them in IRIS shortly.

Now answer the two Step-1 questions from the triage method:

1. *What is this alert claiming happened?* — A brute-force SSH attack against `vic-jump`, targeting the `admin` account, which *eventually succeeded*.
2. *To whom did it claim to happen?* — `vic-jump`, the SSH jumpbox.

You have your foundation. Move to Step 2.

## Step 2 — Investigate

Now we pivot and enrich.

### Switch to IRIS

Click **DFIR-IRIS** in the portal. Log in. (Default credentials are printed by `make first-run-creds` on first run.)

You should see that one or more cases have already been created automatically. The Wazuh → IRIS integration noticed the alert cluster and built a case skeleton for you, observables pre-extracted. This is what happens in real SOCs too — the SIEM hands the case to the SIRP, and the analyst takes it from there.

> **You'll see several cases, not just one — that's normal.** A live lab is always producing ambient noise, and a single attack burst can open more than one case (one per constituent alert). Don't agonize over picking "the" perfect one: **any case whose observables include the attack's source IP `10.50.10.250` (with host `vic-jump` and user `admin`) is the right investigation.** Triage *one* such case to completion and **close exactly that one**; leave the ambient/noise cases — and any duplicate attack cases — open. `make score` grades the case you closed most recently. (More on this in [07 — Using DFIR-IRIS](07-using-iris.md).)

Open one of the attack cases (its IOC list contains `10.50.10.250`). You'll see:

- A title referencing the alert type.
- An **Observables** or **IOCs** section listing the source IP, target host, and target user that were auto-extracted.
- A timeline (mostly empty at this point — you'll fill it in).
- A summary field (empty — you'll write it).

> **Stop and look.** Confirm the observables include the three you noted from Wazuh (source IP, host, user). If any are missing, you can add them manually in IRIS — the auto-extraction is best-effort, not perfect.

### Pivot in time on the affected host

Go back to your Wazuh tab. Filter the alert view by host: only show alerts where the agent is `vic-jump`. Expand the time window to the 60 minutes around the attack.

What do you see in the 60 minutes *before* the brute force? Normal activity — probably some benign noise from the `noise-gen` container. Nothing alarming.

What do you see *after* the successful login? On a real endpoint with command logging (EDR or auditd) you'd now pivot to what the attacker did next — `whoami`, `id`, `sudo -l` — to gauge their intent. **Wachturm's jumpbox doesn't log individual post-login commands, so you won't find a Wazuh alert for them here** — that's a known limitation of this lab, not a hole in your investigation. The compromise is already established by the evidence you *can* see: a sustained burst of failed authentications from one source IP, immediately followed by a successful login from that same IP (the rule 40112 correlation), opening an interactive admin session.

> **Why this matters.** A successful authentication *for the targeted account, from the very IP that just battered it with failures*, is what makes this a high-severity TP and not a low-severity "looks like brute force, ignore." The attacker is now inside with valid admin credentials. In a production SOC your next move is to pivot to their post-login activity; here you note that the lab doesn't surface it and escalate on the confirmed compromise.

Add a note to the IRIS case timeline summarizing what you saw. Something like: "Sustained failed-auth burst from 10.50.10.250 against `admin` on `vic-jump`, immediately followed by a successful login (Wazuh rule 40112) — credential compromise; jumpbox does not log post-login commands."

### Enrich the source IP

Now use Cortex. IRIS v2.4 has no "send to Cortex" button — enrichment is a deliberate pivot (see [08 — Using Cortex](08-using-cortex.md)): note the source-IP observable in your IRIS case, then open **Cortex** separately at `http://127.0.0.1:9001` and log in with the Cortex analyst credentials from `make first-run-creds`.

Run the **`DShield_lookup`** analyzer against the source IP (New Analysis → data type `ip` → paste the value → Start). This keyless analyzer queries the SANS Internet Storm Center for the IP's attack history and works out of the box. In Wachturm this IP is `10.50.10.250` (RFC1918 private), so DShield reports no attack history — itself a valid Tier-1 finding for an internal address. *(If your operator set an `ABUSEIPDB_API_KEY`, you'll also see an optional `AbuseIPDB` analyzer; the keyless `DShield_lookup` and `ValidateObservable` always work.)*

> **Run the analyzer anyway and record the result.** This is the discipline. The habit of "always enrich, even when you expect nothing" is what catches the rare real-world case where the IP *does* have reputation data and the analyzer changes your conclusion.

You'll fold this into your case Summary in Step 4 — something like: "Source IP `10.50.10.250` enriched via DShield — no recorded attack history; consistent with an internal host."

You have now finished Step 2. You read the alert (Step 1), pivoted in time on the target host, pivoted to the post-auth commands, and enriched the source IP (Step 2). You have evidence. Time to decide.

## Step 3 — Decide

Three decisions. Make them deliberately.

### Verdict

The evidence:

- Sustained burst of failed authentication attempts from one source IP.
- A successful authentication for the targeted user from that same source IP, immediately after the failures.
- Reconnaissance commands executed by that user, from that source IP, in the minutes following.

This is the textbook signature of a **brute force compromise**. Verdict: **true positive**. (You'll record this as a `verdict:` case tag in a moment — see *Record your decision in IRIS* below.)

### Severity

A compromised admin account on a jumpbox with attacker-controlled session activity is a serious incident. Someone needs to act *now* — kill the attacker's session, reset credentials, contain the host. Severity: **high**.

(Not critical. Critical would be a domain controller compromise, or active ransomware deployment, or a confirmed breach of customer-facing infrastructure. High is the right rung for "single host compromise, jumpbox, attacker has recon-level access at this moment.")

### Confidence

The evidence is direct and unambiguous: same IP, same user, brute force followed by success followed by recon. There is no other reasonable explanation. Confidence: **high**.

### Record your decision in IRIS — the tag convention

IRIS has no built-in verdict/severity/confidence fields, so Wachturm records them as **case tags**. On your case, add these three tags (the case **tags** field — type each and press Enter):

- `verdict:true_positive`
- `severity:high`
- `confidence:high`

These three tags are how `make score` reads your decision — together they're **70% of the score**, so never skip them. Allowed values (and the ±1-step tolerance on severity/confidence) are in [07 — Using DFIR-IRIS](07-using-iris.md) under "How Wachturm records a verdict."

## Step 4 — Document

Now you write the summary and set next steps. This is where most students under-invest. Don't.

### The summary

Write a paragraph that stands alone — someone reading only this paragraph, without seeing the alert or the timeline, should understand the situation and what to do.

Here's a competent example:

> Between 14:22 and 14:24 UTC, source IP 10.50.10.250 conducted a sustained SSH brute-force attack against the `admin` account on `vic-jump`, the SSH jumpbox: a burst of failed authentications immediately followed by a successful login from the same IP, which Wazuh correlated as rule 40112 ("multiple authentication failures followed by a success"), opening an interactive admin session. Source IP enrichment via DShield returned no recorded attack history (private address range, expected for this lab environment). This represents an active credential compromise of an administrative account. Recommend immediate session termination, credential reset for the admin account, host containment, and Tier 2 escalation for scope-of-impact investigation.

Notice what that paragraph does:

- States the **what** (brute force) with timing.
- States the **who/where** (source IP, target host, target account).
- States the **outcome** (a successful login after the failure burst — credential compromise).
- States what enrichment was attempted and what it produced (or didn't).
- States the **verdict** explicitly.
- States the **recommended next steps**.

A Tier 2 lead can read this in 20 seconds and have all the context they need to take the case.

Type something in this shape into the IRIS case summary field. Use your own words. Mention timestamps; mention specific hostnames and IPs.

### Next steps

IRIS has no dedicated "next steps" field, and the auto-grader doesn't score these separately — so fold your recommended actions into the **case Summary** above (a real analyst summary always ends with them). For this scenario, recommend at least:

- **Contain the host** — isolate `vic-jump` from the network
- **Reset credentials** — invalidate the `admin` password and any associated keys
- **Escalate to Tier 2** — they investigate lateral movement, dwell time, and any other touched assets

### Close the case

Hit the close-case button. Confirm your three tags (`verdict:` / `severity:` / `confidence:`) are set as you intended. Confirm your summary is saved. Submit.

## Score yourself

Back to the terminal:

```bash
make score SCN=SCN-001
```

You'll get a numerical score and a breakdown showing which auto-graded criteria you hit and missed. **Because this walkthrough handed you the verdict, the severity, the confidence, and a model summary, expect a high score here — often the full 100.** That's what a guided first run is for. The real benchmark comes later: on scenarios you work *on your own*, without a walkthrough, **75–95 is a normal first result**, and a 100 usually means you'd seen the pattern before.

Read the breakdown. The auto-grader will tell you specifically what it scored and why. Then go open the instructor companion document for SCN-001 (at `scenarios/SCN-001-ssh-brute-force.instructor.md`) and compare your work to the full solution walkthrough. The instructor doc lists the five most common mistakes — see if you made any of them.

## What you just learned

You learned the four-step triage method by doing it. You used three real tools (Wazuh, IRIS, Cortex) in the way real Tier 1 analysts use them. You made three real decisions (verdict, severity, confidence) and documented them.

You also did one thing that nobody told you to do explicitly but that matters: **you enriched even when you didn't expect the enrichment to be useful.** That's the habit. Keep it.

## What's next

Read **[The Triage Method](03-the-triage-method.md)** all the way through. You just did the four steps; now read the document that explains why each step is structured the way it is. With practice fresh in your hands, the methodology document will land differently than if you'd read it cold.

Then pick any scenario from `make scenarios` and try it on your own, without a walkthrough. That's how the rest of your Tier 1 training works.
