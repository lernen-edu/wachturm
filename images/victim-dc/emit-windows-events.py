#!/usr/bin/env python3
"""vic-dc Windows-shaped event emitter (synthetic; PRD §5).

Appends benign baseline Windows events as JSON lines to
/var/log/win/events.json so the Wazuh agent (localfile log_format json)
ships Windows-shaped telemetry to the manager. This is BASELINE DC noise
only (successful logons, normal process creates) — attack-specific
events are injected by the scenario runner later, not here.

Deliberately minimal/representative (advisor #6 timebox). Stdlib only.
"""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone

OUT = "/var/log/win/events.json"
HOST = "DC01.acme.local"
USERS = ["ACME\\jdoe", "ACME\\asmith", "ACME\\svc-backup"]


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _event() -> dict[str, object]:
    """One benign Windows event: 4624 logon or Sysmon 1 process create."""
    if random.random() < 0.6:  # noqa: S311 - synthetic noise, not crypto
        return {
            "win": {
                "system": {"channel": "Security", "eventID": "4624", "computer": HOST},
                "eventdata": {
                    "targetUserName": random.choice(USERS),  # noqa: S311
                    "logonType": "3",
                    "ipAddress": f"10.50.10.{random.randint(2, 200)}",  # noqa: S311
                },
            }
        }
    return {
        "win": {
            "system": {
                "channel": "Microsoft-Windows-Sysmon/Operational",
                "eventID": "1",
                "computer": HOST,
            },
            "eventdata": {
                "image": random.choice(  # noqa: S311
                    [
                        "C:\\Windows\\System32\\svchost.exe",
                        "C:\\Windows\\System32\\lsass.exe",
                        "C:\\Windows\\explorer.exe",
                    ]
                ),
                "user": random.choice(USERS),  # noqa: S311
            },
        }
    }


def main() -> None:
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    while True:
        rec = _event()
        rec["timestamp"] = _ts()
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        time.sleep(random.uniform(8, 20))  # noqa: S311 - low benign rate


if __name__ == "__main__":
    main()
