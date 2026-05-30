"""Wazuh alerts -> IRIS cases pipeline (P2-M3).

Pure functions over alert lines + injected ``create_case`` / ``add_ioc``
callables; the thin always-on watcher (wachturm.cli ``wazuh-to-iris``)
binds those to the real IRIS client. Decisions are grounded in the
captured fixtures and the advisor review:

* threshold L3 — SCN-003's defining benign signal (rule 5715) is L3, so
  a higher floor would break the "running ANY of SCN-001/002/003
  produces a case" DoD; dedup carries noise suppression, not threshold;
* dedup on (agent, srcip, rule.groups[0]|id) within a 600s window, so a
  brute-force collapses to ONE case and a later unrelated run does not
  glue onto a stale case;
* an observable gate (sharpening "dedup carries suppression"): an alert
  that yields zero IOCs cannot seed a useful triage case, so it is
  skipped;
* per-alert create failures and per-IOC attach failures are swallowed —
  the always-on watcher must never die on one bad record, and a case
  with most of its observables beats no case (partial > none).
"""

import json
import time
from collections.abc import Callable, Iterable
from typing import Any

from wachturm.integrations.observable_extractor import Observable, extract_observables

DEFAULT_MIN_LEVEL = 3
_WINDOW_SECONDS = 600.0

DedupKey = tuple[str, str, str]


def _alerts(lines: Iterable[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in lines:
        text = raw.strip()
        if not text:
            continue
        try:
            obj = json.loads(text)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _subdict(alert: dict[str, Any], key: str) -> dict[str, Any]:
    sub = alert.get(key)
    return sub if isinstance(sub, dict) else {}


def _level(alert: dict[str, Any]) -> int:
    raw = _subdict(alert, "rule").get("level")
    if raw is None:
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def qualifying_alerts(
    lines: Iterable[str], *, min_level: int = DEFAULT_MIN_LEVEL
) -> list[dict[str, Any]]:
    """Alerts at/above ``min_level`` that also yield >=1 observable."""
    out: list[dict[str, Any]] = []
    for alert in _alerts(lines):
        if _level(alert) >= min_level and extract_observables(alert):
            out.append(alert)
    return out


def dedup_key(alert: dict[str, Any]) -> DedupKey:
    """(agent.name, data.srcip, rule.groups[0] or rule.id) — defensive."""
    rule = _subdict(alert, "rule")
    agent = _subdict(alert, "agent")
    data = _subdict(alert, "data")
    groups = rule.get("groups")
    grp = groups[0] if isinstance(groups, list) and groups else rule.get("id", "")

    def _s(value: Any) -> str:
        return value if isinstance(value, str) else ""

    return (_s(agent.get("name")), _s(data.get("srcip")), _s(grp))


def case_payload(alert: dict[str, Any]) -> dict[str, str]:
    """A valid /manage/cases/add payload (CaseSchema minimums) from an alert."""
    rule = _subdict(alert, "rule")
    agent = _subdict(alert, "agent")
    data = _subdict(alert, "data")
    rid = str(rule.get("id") or "?")
    desc = str(rule.get("description") or "Wazuh alert")
    host = str(agent.get("name") or "unknown-host")
    srcip = str(data.get("srcip") or "")
    alert_id = str(alert.get("id") or f"wazuh-{rid}")

    name = f"[Wazuh {rid}] {desc} on {host}"[:180]
    if len(name) < 2:
        name = f"Wazuh alert {rid}"

    lines = [
        f"Auto-created from Wazuh alert {alert_id}.",
        f"Rule {rid} (level {_level(alert)}): {desc}",
        f"Agent/host: {host}",
    ]
    if srcip:
        lines.append(f"Source IP: {srcip}")
    full_log = alert.get("full_log")
    if isinstance(full_log, str) and full_log.strip():
        lines.append(f"Log: {full_log.strip()[:300]}")
    description = "\n".join(lines)
    if len(description) < 2:
        description = "Wazuh alert"
    return {"name": name, "description": description, "soc_id": alert_id}


def process(
    lines: Iterable[str],
    *,
    create_case: Callable[[dict[str, str]], int],
    add_ioc: Callable[[int, Observable], None],
    min_level: int = DEFAULT_MIN_LEVEL,
    state: dict[DedupKey, tuple[int, float]] | None = None,
    now: Callable[[], float] = time.monotonic,
    window_seconds: float = _WINDOW_SECONDS,
) -> list[int]:
    """Create/dedupe IRIS cases for qualifying alerts; attach observables.

    Returns the case ids newly CREATED this call. An in-window dedup hit
    reuses the existing case and just attaches any new observables.
    """
    if state is None:
        state = {}
    created: list[int] = []
    snapshot = now()
    for stale in [k for k, (_, ts) in state.items() if snapshot - ts > window_seconds]:
        del state[stale]

    for alert in qualifying_alerts(lines, min_level=min_level):
        key = dedup_key(alert)
        entry = state.get(key)
        try:
            if entry is not None:
                case_id = entry[0]
            else:
                case_id = create_case(case_payload(alert))
                created.append(case_id)
        except Exception:  # noqa: BLE001 - never let one bad alert kill the watcher
            continue
        state[key] = (case_id, now())
        for obs in extract_observables(alert):
            try:
                add_ioc(case_id, obs)
            except Exception:  # noqa: BLE001 - partial > none; never abort a case
                continue
    return created
