# noise-gen — design contract

> Written **before** the implementation (SM0) so the SM4 code is built to
> satisfy it and can be verified against it. This is the spec; the script
> in this directory (added in SM4) must obey every HARD constraint here.

## Purpose

Generate a realistic ambient stream of **benign** activity (50–100
events/minute) across the victim network so the SOC isn't a ghost town.
The pedagogical point: students must learn to separate a real attack
(a scenario) from background noise. If the lab is silent, triage is
trivial and unrealistic.

## HARD constraints — noise-gen MUST NOT, on its own, ever form a true-positive-shaped pattern

These are non-negotiable. A violation means a scenario's signal gets
polluted and a student is graded against contaminated evidence.

- **SSH:** only *successful* logins as legitimate users, low rate, jittered.
  **Never** failed-auth bursts — must stay far below Wazuh rules 5710 /
  5712 / 5715 thresholds. No auth failures that could read as guessing.
- **Web (vic-web):** only legitimate paths and verbs (`GET /`,
  `/index.html`, `/health`, static assets). **Never** scanner/attack
  shapes: no `/wp-admin`, `/.env`, `/admin`, `/phpmyadmin`, `.git`,
  no SQLi/XSS strings, no 4xx-storm.
- **No network recon shapes:** no port scans, no nmap-style connection
  fans, no host sweeps, nothing Suricata would flag as scan/recon.
- **Package/system activity:** benign apt/update-shaped log lines only.
- **Fixed, identifiable source identity:** noise-gen runs from its own
  container IP on the `victims` network. Scenarios exclude that IP so
  noise can never be mistaken for (or contaminate) a scenario actor.
- **Owned account identity (the account dual of the IP-exclusion rule):**
  noise-gen authenticates as the legitimate `analyst` user
  (`analyst:analyst`) into vic-jump for its benign successful-login
  stream. **Scenarios MUST NOT use the `analyst` account** for
  behavioral/correlation testing — and in particular must never change
  its password or generate failed `analyst` auths. Hijacking it breaks
  the zero-failure SSH invariant above: noise-gen's `sshpass -p analyst`
  then *fails*, flooding Wazuh's `analyst` correlation state and making
  every analyst-touching scenario's expected outcome non-deterministic.
  Scenarios seed and own their own users instead (as SCN-001/SCN-002 do
  with `admin`, SCN-003 with `bobsmith`). _Discovered the hard way in
  SM7: SCN-003 originally seized `analyst`, which made compromise-
  correlation rule 40112 fire on a benign login._
- **Deterministic:** event mix seeded by `NOISE_SEED` (default 42) for
  reproducible runs; rate randomized within 50–100/min around the seed.

## Verification (performed in SM4, evidence in the Phase 1 handoff)

Run noise-gen alone, no scenario, for ≥10 minutes. **Assert ZERO
true-positive-shaped alerts**: no Wazuh 57xx auth-brute alerts, no
web-attack signatures, no Suricata scan/recon alerts. Only then is
noise-gen allowed into the core profile.
