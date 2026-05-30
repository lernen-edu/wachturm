#!/usr/bin/env python3
"""Scenario-driven Suricata EVE alert emitter (Wachturm P3a).

Appends ONE realistic Suricata ``event_type:"alert"`` record to
/var/log/suricata/eve.json — the file Suricata already writes and the
Wazuh manager already ingests (``<localfile> log_format json``), so the
injected alert flows through Wazuh's bundled Suricata ruleset
(/var/ossec/ruleset/rules/0475-suricata_rules.xml, rule ~86601) into a
real Wazuh alert → IRIS case, exactly as a captured packet would.

Why inject instead of capture: Suricata is a passive sidecar on a
Docker **bridge**; a bridge does not deliver peer-to-peer unicast to a
bystander, so live capture sees ~zero victim traffic (P3a spike A,
verified `ipv4=0`). Real packet capture is a network re-architecture
(BUILD_ORDER Phase 5). For v1.0 the NIDS→SIEM→case path is exercised
authentically by emitting the EVE alert the scenario's simulated
traffic *would* have produced — the same accepted model as vic-dc's
Windows events and SCN-001's generated auth.log. The packet source
is simulated; the detection, decode, correlation, case, and triage
are 100% real.

On-demand (a scenario step invokes it), NOT a daemon — network
scenarios emit specific alerts at specific times. Stdlib only; mirrors
images/victim-dc/emit-windows-events.py conventions.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone

OUT = "/var/log/suricata/eve.json"


def _ts() -> str:
    # Suricata EVE timestamp format, e.g. 2026-05-18T01:23:45.123456+0000
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond:06d}+0000"


def _record(a: argparse.Namespace) -> dict[str, object]:
    src_port = a.src_port if a.src_port else random.randint(32768, 60999)  # noqa: S311
    rec: dict[str, object] = {
        "timestamp": _ts(),
        "flow_id": random.randint(10**14, 9 * 10**14),  # noqa: S311
        "in_iface": "any",
        "event_type": "alert",
        "src_ip": a.src,
        "src_port": src_port,
        "dest_ip": a.dest,
        "dest_port": a.dest_port,
        "proto": a.proto,
        # Wazuh ingests eve.json with the generic `json` decoder, which
        # names fields verbatim — so src_ip/dest_ip land as
        # data.src_ip/data.dest_ip, which observable_extractor (reads
        # data.srcip/data.dstip, Wazuh's normalized names) does NOT see,
        # leaving the watcher with no observable -> no IRIS case. These
        # aliases make the generic decoder also yield data.srcip/dstip
        # so the proven observable->watcher->case->scoring path works.
        # Contained to the synthetic emitter (the approved model);
        # observable_extractor stays untouched (v1.1 concern).
        "srcip": a.src,
        "dstip": a.dest,
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": a.sid,
            "rev": 1,
            "signature": a.signature,
            "category": a.category,
            "severity": a.severity,
            "metadata": {
                "created_at": ["2026_05_18"],
                "updated_at": ["2026_05_18"],
            },
        },
    }
    if a.app_proto:
        rec["app_proto"] = a.app_proto
    return rec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wachturm-emit-eve", description=__doc__)
    p.add_argument("--src", required=True, help="source IP (the in-lab actor)")
    p.add_argument("--dest", required=True, help="destination IP (the observable IoC)")
    p.add_argument("--signature", required=True, help="Suricata alert.signature text")
    p.add_argument("--sid", type=int, required=True, help="alert.signature_id")
    p.add_argument("--category", default="Misc activity", help="alert.category")
    p.add_argument("--severity", type=int, default=2, help="alert.severity (1=high)")
    p.add_argument("--proto", default="TCP", help="TCP|UDP|...")
    p.add_argument("--src-port", type=int, default=0, dest="src_port")
    p.add_argument("--dest-port", type=int, default=443, dest="dest_port")
    p.add_argument("--app-proto", default="", dest="app_proto", help="dns|tls|http|…")
    p.add_argument("--count", type=int, default=1, help="emit N identical alerts")
    a = p.parse_args(argv)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # O_APPEND single-line writes are atomic (<PIPE_BUF), safe alongside
    # the live suricata process writing stats to the same file.
    with open(OUT, "a", encoding="utf-8") as fh:
        for _ in range(max(1, a.count)):
            fh.write(json.dumps(_record(a)) + "\n")
    print(f"emit-eve: wrote {max(1, a.count)} alert(s) sid={a.sid} {a.src}->{a.dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
