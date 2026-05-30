"""Portal state — Phase-1 legacy snapshot + Phase-3 live tutor state.

``build_state`` is the *pure* half of SM6: given a finished run it
produces the JSON the portal's ``/api/state`` serves (``pollState`` JS
consumes ``scenario`` + ``elapsed``). The ``docker cp`` into the portal
container is the IO boundary, exercised e2e by ``make scenario``.

P3a-3b: the Phase-3 "state updates as scenarios progress" system
(BUILD_ORDER:155-156) is now implemented via :func:`scenario_state`,
which the wachturm-tutor reads (``references/tool-access.md`` expects
``active_scenario`` + ``scenario_status``). Growth is ADDITIVE — every
legacy key the portal JS consumes is preserved, so these original
tests still pin the back-compat contract; the new tests pin the
Phase-3 schema.
"""

import json

from wachturm.runner import AlertCheck, StepResult, build_state, scenario_state
from wachturm.scenario import Scenario

BASE = {
    "schema_version": "1.0",
    "id": "SCN-901",
    "name": "exec fixture",
    "description": "runner state fixture",
    "author": "Wachturm Contributors",
    "created": "2026-05-16",
    "difficulty": "easy",
    "category": "discovery",
    "expected_verdict": "benign",
    "duration_minutes": 1,
    "steps": [{"actor": "atk-kali", "description": "go", "command": "true"}],
    "expected_alerts": [],
    "answer_key": {"verdict": "benign", "severity": "low", "confidence": "low"},
}


def _scn(**over: object) -> Scenario:
    return Scenario.model_validate({**BASE, **over})


def _ok(step: str = "s") -> StepResult:
    return StepResult(step=step, returncode=0, stdout="", stderr="", ok=True)


def _bad(step: str = "s") -> StepResult:
    return StepResult(step=step, returncode=1, stdout="", stderr="boom", ok=False)


def _check(ok: bool) -> AlertCheck:
    return AlertCheck(rule_id=5760, required=1, seen=1 if ok else 0, timeframe=180, ok=ok)


def test_passed_status_and_core_fields() -> None:
    s = build_state(_scn(), [_ok(), _ok()], [], started=1000.0, finished=1005.0)
    assert s["scenario"] == "SCN-901 — exec fixture"
    assert s["status"] == "passed"
    assert s["elapsed"] == "5s"


def test_failed_status_when_any_step_not_ok() -> None:
    s = build_state(_scn(), [_ok(), _bad()], [], started=1000.0, finished=1003.0)
    assert s["status"] == "failed"


def test_lab_integrity_ok_when_all_checks_ok() -> None:
    s = build_state(_scn(), [_ok()], [_check(True), _check(True)], started=0.0, finished=1.0)
    assert s["lab_integrity"] == "ok"


def test_lab_integrity_fail_when_any_check_not_ok() -> None:
    s = build_state(_scn(), [_ok()], [_check(True), _check(False)], started=0.0, finished=1.0)
    assert s["lab_integrity"] == "fail"


def test_lab_integrity_none_when_alert_checks_none() -> None:
    # No expected_alerts in the scenario → no integrity verdict to report.
    s = build_state(_scn(), [_ok()], None, started=0.0, finished=1.0)
    assert s["lab_integrity"] is None


def test_elapsed_clamps_negative_to_zero() -> None:
    # Clock skew must never render a negative "Elapsed" in the portal.
    s = build_state(_scn(), [_ok()], [], started=1005.0, finished=1000.0)
    assert s["elapsed"] == "0s"


def test_state_is_json_serializable_round_trip() -> None:
    # The dict is docker-cp'd as JSON to the portal. A datetime (instead
    # of an ISO string) would pass the field asserts but break json.dumps.
    s = build_state(_scn(), [_ok()], [_check(True)], started=1000.0, finished=1042.0)
    assert json.loads(json.dumps(s)) == s
    assert isinstance(s["started"], str)
    assert isinstance(s["finished"], str)


# ── Phase-3 live tutor state (P3a-3b) ────────────────────────────────


def test_build_state_additively_carries_tutor_keys() -> None:
    # build_state is now an end-of-run "completed" snapshot that ALSO
    # carries the tutor schema — legacy keys unchanged (asserted above).
    s = build_state(_scn(), [_ok()], [_check(True)], started=1000.0, finished=1042.0)
    assert s["active_scenario"] == "SCN-901"
    assert s["scenario_status"] == "completed"
    assert isinstance(s["scenario_started_at"], str)
    assert isinstance(s["scenario_completed_at"], str)
    assert s["expected_case_id"] is None
    assert s["last_score"] is None
    assert s["hints_used"] == 0
    assert json.loads(json.dumps(s)) == s


def test_scenario_state_running_snapshot() -> None:
    s = scenario_state(_scn(), "running", started=1000.0, hints_used=2)
    assert s["active_scenario"] == "SCN-901"
    assert s["scenario_status"] == "running"
    assert s["scenario_completed_at"] is None
    assert s["hints_used"] == 2
    assert s["scenario"] == "SCN-901 — exec fixture"  # legacy key kept
    assert s["status"] == "running"
    assert json.loads(json.dumps(s)) == s


def test_scenario_state_scored_snapshot_carries_last_score() -> None:
    ls = {"total": 90.0, "possible": 100.0, "pct": 90}
    s = scenario_state(_scn(), "scored", started=1000.0, finished=1100.0, last_score=ls)
    assert s["scenario_status"] == "scored"
    assert s["last_score"] == ls
    assert s["status"] == "scored"
    assert json.loads(json.dumps(s)) == s


def test_scenario_status_is_constrained_to_the_tutor_vocabulary() -> None:
    for st in ("not_started", "running", "completed", "scored"):
        assert scenario_state(_scn(), st, started=1.0)["scenario_status"] == st
