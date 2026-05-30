"""TDD for wachturm.integrations.observable_extractor (P2-M2).

Grounded in REAL captured Wazuh alerts (runner/tests/fixtures/*.jsonl,
one SCN per fresh lab). The SSH-auth scenarios only carry IP/user/host
observables, so file-hash / URL extraction is covered with synthetic
records that mirror the documented Wazuh syscheck/data schema.

Core requirement (Phase-2 risk #2): extract what it can, skip what it
can't, NEVER crash on alert-shape variance.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from wachturm.integrations.observable_extractor import (
    Observable,
    extract_from_lines,
    extract_observables,
    iris_ioc_type,
)

_FX = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> list[str]:
    return (_FX / name).read_text().splitlines()


# ── real fixtures ────────────────────────────────────────────────────


def test_scn001_real_observables_present() -> None:
    obs = extract_from_lines(_fixture("SCN-001.alerts.jsonl"))
    assert isinstance(obs, list)
    assert all(isinstance(o, Observable) for o in obs)
    expect = {
        Observable("ip", "10.50.10.250", "source"),  # atk-kali
        Observable("username", "admin", "target"),  # brute-forced account
        Observable("hostname", "vic-jump", "target"),  # monitored victim
    }
    assert expect <= set(obs)
    assert len(obs) == len(set(obs))  # deduplicated


def test_scn002_real_observables_present() -> None:
    obs = set(extract_from_lines(_fixture("SCN-002.alerts.jsonl")))
    assert Observable("ip", "10.50.10.250", "source") in obs
    assert Observable("username", "admin", "target") in obs


def test_scn003_real_observables_present() -> None:
    obs = set(extract_from_lines(_fixture("SCN-003.alerts.jsonl")))
    assert Observable("username", "bobsmith", "target") in obs
    assert Observable("hostname", "vic-jump", "target") in obs


# ── defensive behaviour (the load-bearing requirement) ───────────────


def test_empty_alert_yields_nothing() -> None:
    assert extract_observables({}) == []


def test_alert_without_data_or_agent_does_not_crash() -> None:
    assert extract_observables({"rule": {"id": "501"}}) == []


def test_non_dict_and_garbage_lines_are_skipped() -> None:
    lines: Iterable[str] = [
        '{"data":{"srcip":"203.0.113.9"}}',
        "this is not json",
        "",
        "[1,2,3]",  # valid JSON but not an alert object
        "42",
        '{"agent":{"name":"vic-web","ip":"10.50.10.10"}}',
    ]
    obs = set(extract_from_lines(lines))
    assert Observable("ip", "203.0.113.9", "source") in obs
    assert Observable("hostname", "vic-web", "target") in obs
    assert Observable("ip", "10.50.10.10", "target") in obs


def test_weird_value_types_skipped_not_crash() -> None:
    alert: dict[str, Any] = {
        "data": {"srcip": 12345, "dstuser": None, "dstip": ""},
        "agent": {"name": "  ", "ip": "10.0.0.1"},
    }
    obs = extract_observables(alert)
    assert Observable("ip", "10.0.0.1", "target") in obs
    # int srcip, None user, empty dstip, blank hostname all dropped
    assert all(o.value.strip() for o in obs)
    assert not any(o.type == "username" for o in obs)


def test_file_hash_and_url_synthetic() -> None:
    alert: dict[str, Any] = {
        "syscheck": {
            "path": "/tmp/x",
            "sha256_after": "a" * 64,
            "md5_after": "b" * 32,
        },
        "data": {"url": "http://malicious.example/x"},
    }
    obs = set(extract_observables(alert))
    assert Observable("file_hash", "a" * 64, "observed") in obs
    assert Observable("file_hash", "b" * 32, "observed") in obs
    assert Observable("url", "http://malicious.example/x", "observed") in obs


def test_dedup_across_many_alerts() -> None:
    same = '{"data":{"srcip":"10.50.10.250","dstuser":"admin"}}'
    obs = extract_from_lines([same] * 25)
    assert obs.count(Observable("ip", "10.50.10.250", "source")) == 1


# ── IRIS IOC type mapping (best-effort; M3 validates vs live IRIS) ────


def test_iris_ioc_type_mapping() -> None:
    assert iris_ioc_type(Observable("ip", "1.2.3.4", "source")) == "ip-src"
    assert iris_ioc_type(Observable("ip", "1.2.3.4", "target")) == "ip-dst"
    assert iris_ioc_type(Observable("hostname", "h", "target")) == "hostname"
    assert iris_ioc_type(Observable("username", "u", "target")) == "account"
    assert iris_ioc_type(Observable("url", "http://x", "observed")) == "url"
    assert iris_ioc_type(Observable("file_hash", "a" * 64, "observed")) == "sha256"
    assert iris_ioc_type(Observable("file_hash", "b" * 32, "observed")) == "md5"
    assert iris_ioc_type(Observable("file_hash", "c" * 40, "observed")) == "sha1"


def test_json_lines_roundtrip_is_stable() -> None:
    # extract_from_lines accepts the exact on-disk fixture format
    raw = _fixture("SCN-001.alerts.jsonl")
    assert any(json.loads(line).get("rule", {}).get("id") == "5760" for line in raw if line)
    assert extract_from_lines(raw)  # non-empty, no exception
