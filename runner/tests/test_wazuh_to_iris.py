"""TDD for the Wazuh->IRIS pipeline (P2-M3 pure logic).

The pipeline is pure functions over alert lines + injected create_case
/ add_ioc callables, so it is fully tested against the REAL captured
fixtures with no lab and no HTTP. The thin always-on watcher loop and
the actual IRIS HTTP are the IO boundary, e2e-verified by the 90s DoD.
"""

import json
from pathlib import Path
from typing import Any

from wachturm.integrations.observable_extractor import Observable
from wachturm.integrations.wazuh_to_iris import (
    case_payload,
    dedup_key,
    process,
    qualifying_alerts,
)

_FX = Path(__file__).parent / "fixtures"


def _lines(name: str) -> list[str]:
    return (_FX / name).read_text().splitlines()


def _first(name: str, rule_id: str) -> dict[str, Any]:
    for ln in _lines(name):
        if ln.strip():
            r: dict[str, Any] = json.loads(ln)
            if r.get("rule", {}).get("id") == rule_id:
                return r
    raise AssertionError(f"{rule_id} not in {name}")


# ── qualifying_alerts ────────────────────────────────────────────────


def test_qualifying_threshold_and_observable_gate() -> None:
    alerts = qualifying_alerts(_lines("SCN-001.alerts.jsonl"), min_level=3)
    assert alerts, "SCN-001 must yield qualifying alerts at L3"
    for a in alerts:
        assert int(a["rule"]["level"]) >= 3
    # every qualifying alert must carry at least one observable
    from wachturm.integrations.observable_extractor import extract_observables

    assert all(extract_observables(a) for a in alerts)


def test_qualifying_high_threshold_narrows() -> None:
    lo = qualifying_alerts(_lines("SCN-001.alerts.jsonl"), min_level=3)
    hi = qualifying_alerts(_lines("SCN-001.alerts.jsonl"), min_level=12)
    assert 0 < len(hi) < len(lo)


def test_qualifying_skips_garbage() -> None:
    out = qualifying_alerts(
        ['{"rule":{"level":7},"data":{"srcip":"1.2.3.4"}}', "nope", ""], min_level=3
    )
    assert len(out) == 1


# ── dedup_key ────────────────────────────────────────────────────────


def test_dedup_key_real_bruteforce_alert() -> None:
    a = _first("SCN-001.alerts.jsonl", "5760")
    assert dedup_key(a) == ("vic-jump", "10.50.10.250", "syslog")


def test_dedup_key_defensive_on_missing() -> None:
    assert dedup_key({}) == ("", "", "")


# ── case_payload ─────────────────────────────────────────────────────


def test_case_payload_satisfies_iris_schema_minimums() -> None:
    a = _first("SCN-001.alerts.jsonl", "5763")
    p = case_payload(a)
    assert len(p["name"]) >= 2 and len(p["description"]) >= 2
    assert isinstance(p["soc_id"], str) and p["soc_id"]
    assert "5763" in p["name"] or "5763" in p["description"]


# ── process ──────────────────────────────────────────────────────────


def _fakes() -> tuple[list[dict[str, str]], list[tuple[int, Observable]], Any, Any]:
    cases: list[dict[str, str]] = []
    iocs: list[tuple[int, Observable]] = []

    def create(payload: dict[str, str]) -> int:
        cases.append(payload)
        return 1000 + len(cases)

    def add(case_id: int, obs: Observable) -> None:
        iocs.append((case_id, obs))

    return cases, iocs, create, add


def test_process_bruteforce_makes_one_case_with_attacker_ioc() -> None:
    cases, iocs, create, add = _fakes()
    created = process(_lines("SCN-001.alerts.jsonl"), create_case=create, add_ioc=add, min_level=10)
    assert len(created) == 1  # 5763/40112 cluster dedups to one case
    cid = created[0]
    assert any(o.value == "10.50.10.250" and o.type == "ip" for _, o in iocs)
    assert all(c == cid for c, _ in iocs)  # all IOCs attached to the one case


def test_process_dedup_same_key_creates_once() -> None:
    cases, iocs, create, add = _fakes()
    same = json.dumps(
        {
            "rule": {"level": 10, "id": "5763", "groups": ["syslog"]},
            "agent": {"name": "vic-jump"},
            "data": {"srcip": "10.50.10.250", "dstuser": "admin"},
        }
    )
    created = process([same, same, same], create_case=create, add_ioc=add, min_level=3)
    assert len(cases) == 1 and len(created) == 1


def test_process_window_eviction_recreates() -> None:
    cases, iocs, create, add = _fakes()
    a = json.dumps(
        {
            "rule": {"level": 10, "id": "5763", "groups": ["syslog"]},
            "agent": {"name": "vic-jump"},
            "data": {"srcip": "9.9.9.9"},
        }
    )
    state: dict[tuple[str, str, str], tuple[int, float]] = {}
    clock = {"t": 1000.0}
    process([a], create_case=create, add_ioc=add, min_level=3, state=state, now=lambda: clock["t"])
    clock["t"] = 1000.0 + 601  # past the 600s window
    process([a], create_case=create, add_ioc=add, min_level=3, state=state, now=lambda: clock["t"])
    assert len(cases) == 2  # stale dedup entry evicted -> new case


def test_process_ioc_failure_does_not_abort_case() -> None:
    cases: list[dict[str, str]] = []

    def create(payload: dict[str, str]) -> int:
        cases.append(payload)
        return 7

    def add(case_id: int, obs: Observable) -> None:
        raise RuntimeError("IRIS rejected this IOC")

    created = process(
        [
            json.dumps(
                {
                    "rule": {"level": 12, "id": "40112", "groups": ["syslog"]},
                    "agent": {"name": "vic-jump"},
                    "data": {"srcip": "10.50.10.250"},
                }
            )
        ],
        create_case=create,
        add_ioc=add,
        min_level=3,
    )
    assert created == [7]  # case still created despite every IOC attach failing


def test_process_below_threshold_creates_nothing() -> None:
    cases, iocs, create, add = _fakes()
    created = process(_lines("SCN-001.alerts.jsonl"), create_case=create, add_ioc=add, min_level=99)
    assert created == [] and cases == []
