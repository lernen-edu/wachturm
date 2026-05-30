"""Tests for the expected_alerts lab-integrity check (SCENARIO_SCHEMA §5).

After a scenario's steps run, the runner reads the Wazuh alerts.json
window and checks each ``expected_alerts`` entry: at least
``minimum_count`` alerts of ``rule_id`` within ``timeframe_seconds`` of
the scenario start. This is a *lab health* check (LAB_INTEGRITY_FAIL),
never student grading. The parser is pure: given alert records + the
spec, decide pass/fail — testable without a live Wazuh.
"""

from typing import Any

from wachturm.runner import AlertCheck, check_expected_alerts
from wachturm.scenario import ExpectedAlert


def _alert(rule_id: int, ts: float) -> dict[str, Any]:
    # Shape mirrors a Wazuh alerts.json record (only fields we read).
    return {"rule": {"id": str(rule_id)}, "ts": ts}


def test_pass_when_min_count_met_within_timeframe() -> None:
    spec = [ExpectedAlert(rule_id=5716, minimum_count=3, timeframe_seconds=60)]
    alerts = [_alert(5716, t) for t in (5.0, 10.0, 40.0)]
    ok, checks = check_expected_alerts(spec, alerts, since_ts=0.0)
    assert ok is True
    assert checks[0] == AlertCheck(rule_id=5716, required=3, seen=3, timeframe=60, ok=True)


def test_fail_when_below_min_count() -> None:
    spec = [ExpectedAlert(rule_id=5720, minimum_count=2, timeframe_seconds=60)]
    ok, checks = check_expected_alerts(spec, [_alert(5720, 5.0)], since_ts=0.0)
    assert ok is False
    assert checks[0].seen == 1
    assert checks[0].ok is False


def test_alerts_outside_timeframe_do_not_count() -> None:
    spec = [ExpectedAlert(rule_id=5715, minimum_count=1, timeframe_seconds=30)]
    # since_ts=100 -> only alerts at >=100 and <=130 count; 95 is before, 200 is after.
    alerts = [_alert(5715, 95.0), _alert(5715, 200.0)]
    ok, checks = check_expected_alerts(spec, alerts, since_ts=100.0)
    assert ok is False
    assert checks[0].seen == 0


def test_overall_ok_only_if_every_expected_alert_passes() -> None:
    spec = [
        ExpectedAlert(rule_id=5716, minimum_count=1, timeframe_seconds=60),
        ExpectedAlert(rule_id=5715, minimum_count=1, timeframe_seconds=60),
    ]
    alerts = [_alert(5716, 3.0)]  # 5715 never fires
    ok, checks = check_expected_alerts(spec, alerts, since_ts=0.0)
    assert ok is False
    assert [c.ok for c in checks] == [True, False]


def test_empty_expected_alerts_is_vacuously_ok() -> None:
    ok, checks = check_expected_alerts([], [_alert(1, 1.0)], since_ts=0.0)
    assert ok is True
    assert checks == []
