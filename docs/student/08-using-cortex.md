# 08 — Using Cortex

Cortex is your enrichment engine. Where Wazuh tells you *what happened* and IRIS records *what you decided*, Cortex helps you answer **"what context can I add to make this decision more confidently?"**

## How enrichment works in Wachturm (read this first)

DFIR-IRIS v2.4 does **not** ship a Cortex module — there is no "send to Cortex" button inside an IRIS case (Cortex is historically TheHive's companion, not IRIS's). Wachturm's enrichment workflow is therefore an explicit, deliberate **pivot**, and it is a realistic one — plenty of real SOCs run their SIRP and their analyzer engine side by side:

1. In your IRIS case, note the observable you want to enrich (e.g. the source IP).
2. Open **Cortex** at **`http://127.0.0.1:9001`** (plain HTTP, loopback — *not* HTTPS).
3. Log in with the Cortex analyst credentials from **`make first-run-creds`** (organization **`wachturm`**).
4. Run an analyzer on the observable (below).
5. Read the result, then **write the conclusion back into your IRIS case Summary.** Always record what you found — it's the discipline, and in real work the enrichment you don't write down didn't happen. (Some scenarios require evidence of enrichment in your summary for credit; others — like the SCN-001 walkthrough — credit it by default. Build the habit regardless.) See [07 — Using DFIR-IRIS](07-using-iris.md), "Writing the case Summary."

That last step closes the loop: Cortex tells you something; IRIS is where it counts.

## What Cortex does

Cortex runs **analyzers** against **observables**. An *observable* is a piece of data you want to look up (IP, domain, hash, URL, email). An *analyzer* queries some source about that observable and returns a structured report. You pick an observable and an analyzer; Cortex runs the analyzer in a throwaway container and hands back a report.

To run one: **New Analysis** → choose the data type (e.g. `ip`) → paste the value → select the analyzer → **Start**. The job appears in **Jobs**; open it when it finishes to read the report.

## The analyzers configured in Wachturm

Phase 2 enables two **keyless** analyzers — they need no account and work out of the box:

- **`ValidateObservable`** — classifies and validates the observable (is it a well-formed IP? a private/RFC1918 address? a public one?). It always returns a result, for any input. The dependable baseline.
- **`DShield_lookup`** — queries the SANS Internet Storm Center for an IP's attack history. A "not listed / 0 attacks" answer on an internal host is itself a valid Tier-1 finding ("no external threat-intel hits, consistent with an internal address").

One more is **opt-in**: **`AbuseIPDB`** (community-reported IP abuse, free tier, 1000 lookups/day) appears only if the operator set `ABUSEIPDB_API_KEY` in `.env` before `make up-casemgmt`. If you don't see it, it isn't configured — that's expected, not a fault.

> The real-MISP analyzer (`MISP`) is intentionally left unconfigured — it is the slot a future Phase wires to a live MISP server. VirusTotal/other public services are not part of the Phase-2 keyless set.

## The Wachturm-specific reality: internal observables

Most IPs in Wachturm scenarios are **internal / RFC1918** (10.x.x.x). Public-reputation services have nothing to say about internal IPs — but the two configured analyzers are chosen so you *still get a meaningful answer*: `ValidateObservable` tells you it's a valid private address; `DShield_lookup` tells you it has no public attack history. **Run the analyzer anyway and record the result.** The triage method says "always enrich, even when you expect little." In a real environment the same habit catches the rare external case; building it here transfers to real work.

A good case-Summary line after enrichment:
*"Source 10.50.10.250 enriched via DShield — no recorded attack reports; ValidateObservable confirms RFC1918. Consistent with an internal host being used as the attack origin, not external infrastructure."*

## How to read an analyzer result

- **Taxonomies** — short, colour-coded summary labels (green = clean/info, yellow = suspicious, red = malicious). Read these first; usually they're enough.
- **Summary / report body** — the detailed findings (scores, related data, dates).
- **Raw output** — the underlying API response, for when you need to dig.

Go deeper than the taxonomy only when the result is surprising or you must defend the call in your write-up.

## Common Cortex pitfalls

- **Treating an empty/clean result as "proven safe."** "We found nothing" ≠ "it is clean." Fresh attacker infrastructure is often uncatalogued.
- **Treating one analyzer's verdict as the decision.** Analyzer output is an *input*. The decision is still yours — a bad-reputation IP can still be doing legitimate things, and a clean one can still be the attacker (as it is in most Wachturm scenarios).
- **Enriching but never recording it in IRIS.** If the finding isn't in the case Summary, it didn't happen as far as the case file — and the grader — are concerned.
- **Running every analyzer "to be thorough."** Pick the analyzer that answers the question you have. Extra runs burn the AbuseIPDB daily quota and clutter nothing useful.

## What Cortex isn't

Cortex doesn't *decide* anything and it doesn't *monitor* — it answers specific questions you ask about a specific observable. The "something happened" signal comes from Wazuh; Cortex is the resource you consult once you have a thing to ask about; IRIS is where the answer becomes part of the record.
