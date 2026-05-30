# 01 — Orientation

Before you triage your first alert, you need to know where things live and what they do. This is a five-minute read.

## What Wachturm is, from your seat

Wachturm is a simulated corporate network with a complete security operations stack monitoring it. Things happen on the network — some malicious, some benign, some that look malicious but aren't. Alerts fire. Your job is to figure out what each alert means and what to do about it.

You are sitting in the analyst's chair. The same tools real Tier 1 analysts use are here, running on your laptop. The work is the same; the stakes are simulated.

## The geography

When you open `http://localhost:8000` you see the Wachturm portal. It is the equivalent of the bookmark bar a real SOC analyst keeps — every tool you need is one click away. The portal also shows you whether each tool is up.

The tools, in the order you'll use them:

**Wazuh** (`https://127.0.0.1:8443`) — your **SIEM**, your Security Information and Event Management platform. This is where alerts are born. When something happens on a monitored host or on the network, Wazuh ingests the log, matches it against its detection rules, and produces an alert. Wazuh is your *first* stop for every scenario. You will spend most of your investigation time here.

**DFIR-IRIS** (`https://127.0.0.1:9000`) — your **case management** system, sometimes called a SIRP (Security Incident Response Platform). When Wazuh produces a noteworthy alert, an integration creates a case in IRIS. The case is the file folder for your investigation: observables, timeline, your notes, your verdict, your case summary. **Every scenario ends with a closed IRIS case.** Always. If you didn't close a case in IRIS, you didn't finish.

**Cortex** (`http://127.0.0.1:9001`) — your **enrichment engine**. Cortex runs *analyzers* against *observables*. You hand it an IP address and it tells you whether that IP has a history of attacks elsewhere; you hand it a file hash and it tells you whether that file is known malware. (Which analyzers are actually available depends on your lab's configuration — see [08 — Using Cortex](08-using-cortex.md).) Cortex's job is to help you answer "what context can I add to make this decision more confidently?"

**Shuffle** (`localhost:3001`, Phase 4+) — your **SOAR**, security orchestration and automated response. Shuffle runs playbooks: "when X happens, do Y automatically." You won't author playbooks as a Tier 1 analyst, but you'll see their results in your IRIS cases (auto-enrichment, auto-tagging).

**MISP** (`localhost:8080`, Phase 4+) — your **threat intelligence** platform. MISP holds IoCs (indicators of compromise) from public feeds and your own team's intel. Cortex queries MISP when you run analyzers; you may also browse MISP directly to check whether an observable from your case appears in a known campaign.

## The "victim" network you're protecting

Wachturm simulates a small corporate environment with these hosts:

- `vic-web` — a public-facing web server. The thing customers reach.
- `vic-work` — an employee workstation. The thing a person uses to do their job.
- `vic-jump` — a jumpbox / bastion host. The thing admins use to reach internal systems from outside.
- `vic-dc` — a stand-in "domain controller." (Real Wachturm uses a Linux container that emits Windows-style logs for learning purposes.)

When you see one of these hostnames in an alert, that's the asset involved.

## The "attacker" you're up against

There is one attacker container, `atk-kali`. It executes scripted attacks according to whichever scenario you ran with `make scenario`. It cannot reach the internet; it cannot reach you. The attacks it performs are real attacks against the victims, just contained.

## Where alerts go to die

This matters: an alert is **not finished** until you have closed an IRIS case with a verdict and a summary. Closing the Wazuh alert by itself accomplishes nothing — Wazuh alerts don't really "close." The IRIS case is the unit of work. Your shift is measured in closed cases, not viewed alerts.

This is true of real SOCs too. You won't write that line on your resume, but it's the operational truth.

## Now what?

Open the portal (`http://localhost:8000`). Confirm Wazuh and IRIS both show "Online." If they don't, get them running before proceeding.

When the portal looks green, move to **[Your First Shift](02-first-shift.md)**.
