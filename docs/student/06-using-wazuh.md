# 06 — Using Wazuh

Wazuh is your SIEM (Security Information and Event Management platform). It is also your HIDS (host intrusion detection — via agents on the victim hosts) and your light EDR (endpoint detection and response — same agents). Three roles, one tool. Wazuh is the primary place you'll work; every triage starts here.

## What Wazuh does

Wazuh has three jobs:

1. **Collects logs** from the victim hosts and from Suricata's network sensor.
2. **Runs detection rules** against those logs in real time. When a log matches a rule, Wazuh emits an alert.
3. **Stores and indexes** the alerts and the underlying log data so you can search both.

Access: **`https://127.0.0.1:8443`** (Wazuh uses HTTPS even locally; the self-signed-certificate browser warning is expected — proceed past it; `make trust-certs` removes it if you prefer). Log in with the Wazuh dashboard credentials printed by **`make first-run-creds`** (`admin` / `SecretPassword` on a default build). If `8443` is already taken on your machine, the lab's port is whatever `WAZUH_DASHBOARD_PORT` is set to in your `.env` — `make first-run-creds` always prints the live URL.

The dashboard is an OpenSearch-Dashboards-derived UI: the **Wazuh menu** (top-left ☰) is where you switch between the views below; the alert table has a query/filter bar and a time-range picker you'll live in.

## The views you'll use

Wazuh's dashboard has many views. As a Tier 1 analyst, you'll use a small subset constantly and the rest rarely.

### Threat Hunting / Security Events

This is your home view. It shows the live stream of alerts, filterable by host, time, rule, source IP, user, and other fields. Every triage starts here.

When you open this view at the start of a scenario, you're looking for:

- **What cluster of alerts is new?** (compared to the baseline noise)
- **Which host(s) are affected?**
- **What time window did the activity occur in?**

The filter and time-window controls are the muscle memory you need to build. Filter to one host. Filter to one source IP. Filter to one rule. Combine filters. Adjust the time window. Iterate.

### Agents

Lists the Wazuh agents enrolled on victim hosts and their status. You'll use this once at first-shift to confirm agents are healthy. After that, you'll only revisit it if a host seems to be "missing" from your investigation — which usually means its agent died, not that nothing happened.

### Rules

The library of detection rules Wazuh is using. As a Tier 1 analyst you generally don't modify rules; you observe what they catch. But knowing *which* rule fired is useful context — a rule named "SSHD authentication failed" tells you something different than a rule named "Multiple authentication failures." Sometimes you'll click into a rule to read its description and understand what it's actually looking for.

### Discover / Raw logs

When the alert view doesn't tell you enough, you go to raw logs. This is the layer below alerts — the actual log lines that did (or did not) trigger detections. You'll use this for:

- Investigating activity that *didn't* trigger an alert but happened around the time something else did.
- Reading the exact log line a rule matched, to confirm it really means what you think it means.
- Pivoting to a host's activity in a window where no alerts fired.

The raw log view feels overwhelming the first time. It's a fire hose. You make it usable by filtering aggressively — by host, by time window, by log source, by keyword.

## Pivot patterns specific to Wazuh

The triage method talks about pivoting in general terms. Here's what those pivots look like in Wazuh specifically:

**Pivot in time on a host:**
1. In Threat Hunting, filter by agent name (e.g., `vic-jump`).
2. Set the time picker to "30 minutes before" through "30 minutes after" the alert of interest.
3. Read every alert in that window.

**Pivot by source IP:**
1. Filter by the source IP field (`data.srcip` or similar — Wazuh's field names vary by data source).
2. Remove all other filters.
3. See every alert across every host involving this source.

**Pivot to raw logs around an alert:**
1. Note the timestamp and the host from the alert.
2. Go to Discover.
3. Filter by `agent.name` and a tight time window (±5 minutes around the alert).
4. Read.

You will not memorize these the first time. You will memorize them by the tenth time.

## Rule severities in Wazuh

Wazuh assigns each rule a severity (level 0–15). Higher number = more severe. Rules at level 12+ are usually treated as urgent by default; rules at level 5–11 are routine but worth attention; rules below 5 are usually informational.

**Important:** Wazuh's rule severity is *Wazuh's opinion*, not the verdict severity you set in IRIS. They're related but not the same. A rule fires at level 12 because Wazuh thinks the pattern is serious *in general*. Your severity in IRIS reflects *this specific case after you investigated it*. A level-12 rule that's an FP gets a low-severity FP in IRIS; that's correct.

## Common Wazuh pitfalls

- **Trusting the alert title without reading the body.** The title is a summary; the body has the specifics. Read the body.
- **Filtering by only one dimension.** A filter for "source IP = X" without a time window can return weeks of unrelated activity. Combine filters.
- **Ignoring Suricata alerts.** Suricata's network detections appear in the same alert stream as Wazuh's host-level detections. They're easy to miss because the rule format looks different. Pay attention to them — network-side evidence is often the most decisive.
- **Refreshing constantly.** The dashboard auto-refreshes. Hammering the refresh button doesn't make new alerts arrive faster.

## What Wazuh isn't

Wazuh is not where investigations live. **The investigation lives in IRIS.** Wazuh tells you *what fired*; IRIS tells you *what you decided about it*. After you've done your Wazuh work for a case, return to IRIS to document and close.

A common new-analyst pattern is to do everything in Wazuh and forget IRIS exists. Resist this. The act of moving from "Wazuh tells me what" to "IRIS records what I decided" is the moment the case becomes work-product instead of curiosity.
