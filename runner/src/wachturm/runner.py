"""Scenario step executor — host-side ``docker exec`` orchestration.

The runner runs on the host and drives containers via ``docker exec``
(SCENARIO_SCHEMA §4/§8). The subprocess boundary is injected
(``execute``/``sleep``) so the control flow is unit-testable without a
live Docker; :func:`run_plan` builds the real commands and the default
executor in the CLI layer wires them to ``subprocess``.

No ``from __future__ import annotations`` (same Typer/Pydantic-adjacent
rationale as the rest of the package).
"""

import shlex
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from wachturm.scenario import ExpectedAlert, Scenario

# (argv, timeout_seconds) -> (returncode, stdout, stderr)
Executor = Callable[[list[str], int], tuple[int, str, str]]
SleepFn = Callable[[float], None]

_SSH_OPTS = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=8"


@dataclass
class StepResult:
    """Outcome of one setup action or step."""

    step: str
    returncode: int
    stdout: str
    stderr: str
    ok: bool


def _argv(actor: str, command: str, via: str, from_: str | None, as_user: str | None) -> list[str]:
    """Build the host ``docker exec`` argv for one action.

    * ``direct``  — exec the command inside ``actor`` (optionally as a user).
    * ``ssh``/``rce_sim`` — exec FROM ``from_``, reaching ``actor`` over
      ssh as ``as_user`` (the schema requires ``from`` when via != direct).
    """
    if via == "direct":
        base = ["docker", "exec"]
        if as_user:
            base += ["-u", as_user]
        return [*base, actor, "sh", "-lc", command]

    user = as_user or "root"
    remote = f"ssh {_SSH_OPTS} {user}@{actor} {shlex.quote(command)}"
    # `from_` is guaranteed non-None by the Step schema validator.
    return ["docker", "exec", str(from_), "sh", "-lc", remote]


def run_plan(
    scn: Scenario,
    *,
    execute: Executor,
    sleep: SleepFn,
    between_setup_and_steps: Callable[[], None] | None = None,
) -> list[StepResult]:
    """Run a scenario's setup then its steps, in order.

    Setup actions run first (SCENARIO_SCHEMA §8), each as a direct exec.
    ``between_setup_and_steps`` (if given) fires exactly once after the
    last setup action and before the first step — the CLI uses it to
    snapshot the Wazuh alerts.json offset so setup noise can't
    contaminate the expected_alerts integrity window. Steps then run in
    order; ``delay_seconds`` pauses *before* the step;
    ``timeout_seconds`` is passed to the executor; ``expect_failure``
    inverts the success condition. Returns one StepResult per step.
    """
    for action in scn.setup:
        execute(_argv(action.actor, action.command, "direct", None, None), 30)

    if between_setup_and_steps is not None:
        between_setup_and_steps()

    results: list[StepResult] = []
    for step in scn.steps:
        if step.delay_seconds:
            sleep(step.delay_seconds)
        argv = _argv(step.actor, step.command, step.via, step.from_, step.as_user)
        rc, out, err = execute(argv, step.timeout_seconds)
        ok = (rc != 0) if step.expect_failure else (rc == 0)
        results.append(
            StepResult(step=step.description, returncode=rc, stdout=out, stderr=err, ok=ok)
        )
    return results


def parse_wazuh_timestamp(ts: str) -> float:
    """Parse a Wazuh alerts.json ``timestamp`` to an absolute POSIX epoch.

    Wazuh emits tz-aware ISO8601 (e.g. ``2026-05-16T23:31:51.123+0000``).
    Parsing must be tz-aware: a naive ``time.mktime`` reads it as local
    time and shifts every alert out of the integrity window vs. a UTC
    ``time.time()`` baseline (the bug the SM5 e2e gate exposed). Returns
    0.0 for anything unparseable so the caller can simply skip it.
    """
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(ts, fmt).timestamp()
        except ValueError:
            continue
    return 0.0


@dataclass
class AlertCheck:
    """Per-expected-alert lab-integrity result (SCENARIO_SCHEMA §5)."""

    rule_id: int
    required: int
    seen: int
    timeframe: int
    ok: bool


def check_expected_alerts(
    expected: list[ExpectedAlert],
    alerts: list[dict[str, Any]],
    *,
    since_ts: float,
) -> tuple[bool, list[AlertCheck]]:
    """Verify each expected alert fired enough times in its timeframe.

    ``alerts`` are Wazuh alerts.json records (we read ``rule.id`` and a
    numeric ``ts``); only alerts in ``[since_ts, since_ts+timeframe]``
    count. Returns ``(overall_ok, per_alert_checks)``. Empty
    ``expected`` is vacuously ok. This gates LAB_INTEGRITY, not grading.
    """
    checks: list[AlertCheck] = []
    for exp in expected:
        seen = 0
        for rec in alerts:
            rule = rec.get("rule") or {}
            if str(rule.get("id")) != str(exp.rule_id):
                continue
            ts = rec.get("ts")
            if ts is None:
                continue
            if since_ts <= float(ts) <= since_ts + exp.timeframe_seconds:
                seen += 1
        checks.append(
            AlertCheck(
                rule_id=exp.rule_id,
                required=exp.minimum_count,
                seen=seen,
                timeframe=exp.timeframe_seconds,
                ok=seen >= exp.minimum_count,
            )
        )
    return (all(c.ok for c in checks), checks)


_TUTOR_STATUSES = ("not_started", "running", "completed", "scored")


def scenario_state(
    scn: Scenario,
    status: str,
    *,
    started: float | None = None,
    finished: float | None = None,
    results: list[StepResult] | None = None,
    alert_checks: list[AlertCheck] | None = None,
    hints_used: int = 0,
    last_score: dict[str, Any] | None = None,
    expected_case_id: int | None = None,
) -> dict[str, Any]:
    """Phase-3 live portal/tutor ``/api/state`` (BUILD_ORDER:155-156).

    ``status`` is the wachturm-tutor vocabulary (``not_started`` |
    ``running`` | ``completed`` | ``scored``; see
    ``skills/wachturm-tutor/references/tool-access.md``). ``closed`` is
    deliberately NOT produced here — the tutor derives that from its own
    read-only IRIS query (it cannot be observed from the runner, which
    never sees the student close their case in the IRIS UI).

    Growth over the Phase-1 stub is strictly **additive**: every legacy
    key the portal ``pollState`` JS consumes (``scenario``, ``status``,
    ``elapsed``, ``started``, ``finished``, ``lab_integrity``) is still
    present with unchanged meaning. The dict is JSON-serializable (it is
    docker-cp'd into the portal container).
    """

    def _iso(t: float | None) -> str | None:
        return datetime.fromtimestamp(t, tz=UTC).isoformat() if t is not None else None

    if started is not None and finished is not None:
        elapsed = f"{max(0, round(finished - started))}s"
    else:
        elapsed = "—"

    integrity: str | None
    if alert_checks is None:
        integrity = None
    else:
        integrity = "ok" if all(c.ok for c in alert_checks) else "fail"

    # Legacy `status` keeps the portal contract: a *completed* run maps
    # to passed/failed from the step results; other lifecycle points
    # mirror the tutor word.
    if status == "completed" and results is not None:
        legacy_status = "passed" if all(r.ok for r in results) else "failed"
    else:
        legacy_status = status

    return {
        # ── legacy (portal pollState JS — never rename/repurpose) ──
        "scenario": f"{scn.id} — {scn.name}",
        "status": legacy_status,
        "elapsed": elapsed,
        "started": _iso(started),
        "finished": _iso(finished),
        "lab_integrity": integrity,
        # ── Phase-3 tutor schema (references/tool-access.md) ──
        "active_scenario": scn.id,
        "scenario_status": status,
        "scenario_started_at": _iso(started),
        "scenario_completed_at": _iso(finished),
        "expected_case_id": expected_case_id,
        "last_score": last_score,
        "hints_used": hints_used,
    }


def build_state(
    scn: Scenario,
    results: list[StepResult],
    alert_checks: list[AlertCheck] | None,
    *,
    started: float,
    finished: float,
) -> dict[str, Any]:
    """End-of-run (``completed``) snapshot. Back-compat shim over
    :func:`scenario_state` so existing callers/tests are unchanged while
    gaining the additive Phase-3 tutor keys."""
    return scenario_state(
        scn,
        "completed",
        started=started,
        finished=finished,
        results=results,
        alert_checks=alert_checks,
    )
