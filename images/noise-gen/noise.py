#!/usr/bin/env python3
"""noise-gen — benign ambient activity generator for Wachturm.

Implements ``images/noise-gen/README.md`` (the binding design contract,
written at SM0 so this code is built to satisfy it).

HARD constraints honored, by construction:

* **SSH:** only *successful* logins as the legitimate ``analyst`` user
  into ``vic-jump`` — the only victim running sshd (vic-work/vic-dc are
  agent-only). The password is always correct, so there are *zero* auth
  failures: structurally impossible to approach Wazuh rules
  5710/5712/5715 (sshd auth-failure / brute-force).
* **Web:** only ``GET`` of confirmed-present, 200-returning paths on
  vic-web (``/``, ``/index.html``, ``/health``). No scanner paths, no
  SQLi/XSS strings, no 4xx storm.
* **No recon shapes:** only ever connects to the two known, listening
  services. No port scans, host sweeps, or connection fans.
* **Package/system activity:** read-only ``apt list``/``uptime``-style
  commands over the SSH session — apt/update-shaped log lines, zero
  side effects.
* **Fixed identity:** noise-gen has a pinned ``victims`` IP (compose);
  SM5 scenarios exclude it so noise can never be mistaken for, or
  contaminate, a scenario actor.
* **Owned account:** authenticates as ``analyst`` (``analyst:analyst``)
  for the benign success stream. Scenarios MUST NOT use or re-password
  the ``analyst`` account — doing so breaks the zero-failure invariant
  above and contaminates Wazuh correlation state (the account dual of
  the IP-exclusion rule; see README.md, discovered in SM7).
* **Deterministic:** a single ``random.Random(NOISE_SEED)`` drives both
  the event mix and the jitter; rate held within 50–100/min.
"""

from __future__ import annotations

import os
import random
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

VIC_JUMP = "10.50.10.30"  # only sshd-bearing victim; demo user analyst:analyst
VIC_WEB = "10.50.10.10"  # nginx; only the confirmed 200 paths below
WEB_PATHS = ("/", "/index.html", "/health")

# Benign, strictly read-only remote commands. They produce ordinary
# successful-auth + system/apt-shaped log lines with no side effects.
SSH_CMDS = (
    "true",
    "uptime",
    "id",
    "whoami",
    "hostname",
    "ls -la /home/analyst",
    "cat /etc/os-release",
    "apt list --installed 2>/dev/null | head -n 20",
)

_STOP = False


def _sigterm(_signum: int, _frame: object) -> None:
    # Make `make noise-stop` (SIGTERM) and Ctrl-C exit promptly.
    global _STOP
    _STOP = True


def log(kind: str, target: str, result: str) -> None:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"{ts} | {kind:<4} | {target:<26} | {result}", flush=True)


def ssh_login(rng: random.Random) -> None:
    cmd = rng.choice(SSH_CMDS)
    argv = [
        "sshpass",
        "-p",
        "analyst",
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "ConnectTimeout=6",
        "-o",
        "LogLevel=ERROR",
        f"analyst@{VIC_JUMP}",
        cmd,
    ]
    try:
        r = subprocess.run(argv, capture_output=True, timeout=15)
        log("ssh", f"analyst@{VIC_JUMP}", f"rc={r.returncode} `{cmd}`")
    except subprocess.TimeoutExpired:
        # A connect timeout (e.g. victim still starting) is one attempt
        # to a known service — not a scan shape. Logged, not fatal.
        log("ssh", f"analyst@{VIC_JUMP}", "skip(timeout)")


def web_get(rng: random.Random) -> None:
    path = rng.choice(WEB_PATHS)
    argv = [
        "curl",
        "-s",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code}",
        "--max-time",
        "6",
        f"http://{VIC_WEB}{path}",
    ]
    try:
        r = subprocess.run(argv, capture_output=True, timeout=10, text=True)
        log("web", f"{VIC_WEB}{path}", f"http={r.stdout.strip() or '000'}")
    except subprocess.TimeoutExpired:
        log("web", f"{VIC_WEB}{path}", "skip(timeout)")


def main() -> int:
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigterm)

    seed = int(os.environ.get("NOISE_SEED", "42"))
    base_epm = int(os.environ.get("NOISE_EVENTS_PER_MIN", "60"))
    rng = random.Random(seed)
    log("init", "noise-gen", f"seed={seed} base_epm={base_epm} (clamped 50-100/min)")

    n = 0
    while not _STOP:
        t0 = time.monotonic()
        # Deterministic benign mix: ambient web-heavy, lighter SSH.
        # Both branches are strictly benign, so the stream cannot, on
        # its own, form a true-positive-shaped pattern.
        if rng.random() < 0.65:
            web_get(rng)
        else:
            ssh_login(rng)
        n += 1

        # Per-event target pace is a fresh seeded draw centred on
        # NOISE_EVENTS_PER_MIN and clamped to the contract band — this
        # *is* the deterministic jitter (reproducible, not metronomic).
        # Subtract the event's own execution time so the realized
        # cadence stays in [50,100]/min rather than band+exec (SM4 v1
        # ignored exec time and drifted to ~40/min, below the floor).
        target_epm = min(100, max(50, base_epm + rng.randint(-15, 15)))
        remaining = (60.0 / target_epm) - (time.monotonic() - t0)
        end = time.monotonic() + max(0.0, remaining)
        while not _STOP and time.monotonic() < end:
            time.sleep(min(0.5, max(0.0, end - time.monotonic())))

    # Final line carries the generated-event count — the SM4 zero-TP
    # verification asserts this is non-trivial (traffic actually ran)
    # *and* that zero TP-shaped alerts fired.
    log("exit", "noise-gen", f"events_generated={n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
