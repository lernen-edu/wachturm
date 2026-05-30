"""Tests for the scenario step executor (SCENARIO_SCHEMA §4 / §8).

The runner shells out to ``docker exec`` on the host. That boundary is
the one unavoidable mock: tests inject a fake executor + fake sleep
(dependency injection) and assert the *constructed commands*, ordering,
delay, timeout, via-ssh form, as_user, and expect_failure semantics —
real control-flow behavior, not mock interactions.
"""

from wachturm.runner import StepResult, run_plan
from wachturm.scenario import Scenario

BASE = {
    "schema_version": "1.0",
    "id": "SCN-901",
    "name": "exec fixture",
    "description": "runner executor fixture",
    "author": "Wachturm Contributors",
    "created": "2026-05-16",
    "difficulty": "easy",
    "category": "discovery",
    "expected_verdict": "benign",
    "duration_minutes": 1,
    "expected_alerts": [],
    "answer_key": {"verdict": "benign", "severity": "low", "confidence": "low"},
}


def _scn(**over: object) -> Scenario:
    return Scenario.model_validate({**BASE, **over})


class FakeExec:
    """Records (argv, timeout) calls; returns a scripted (rc, out, err)."""

    def __init__(self, rc: int = 0) -> None:
        self.calls: list[tuple[list[str], int]] = []
        self.rc = rc

    def __call__(self, argv: list[str], timeout: int) -> tuple[int, str, str]:
        self.calls.append((argv, timeout))
        return (self.rc, "", "")


def test_direct_step_builds_docker_exec_argv() -> None:
    scn = _scn(steps=[{"actor": "atk-kali", "description": "scan", "command": "nmap -p22 x"}])
    ex = FakeExec()
    results = run_plan(scn, execute=ex, sleep=lambda _s: None)

    assert len(ex.calls) == 1
    argv, timeout = ex.calls[0]
    assert argv[:3] == ["docker", "exec", "atk-kali"]
    assert "nmap -p22 x" in argv[-1]
    assert timeout == 30  # schema §4 default
    assert isinstance(results[0], StepResult)
    assert results[0].ok is True


def test_steps_run_in_order_with_delay() -> None:
    scn = _scn(
        steps=[
            {"actor": "atk-kali", "description": "one", "command": "echo 1"},
            {
                "actor": "atk-kali",
                "description": "two",
                "command": "echo 2",
                "delay_seconds": 7,
                "timeout_seconds": 99,
            },
        ]
    )
    ex = FakeExec()
    slept: list[float] = []
    run_plan(scn, execute=ex, sleep=lambda s: slept.append(s))

    assert [c[0][-1].split()[-1] for c in ex.calls] == ["1", "2"]  # order preserved
    assert ex.calls[1][1] == 99  # timeout_seconds passed through
    assert 7 in slept  # delay_seconds honored before step 2


def test_via_ssh_runs_from_the_from_actor_as_user() -> None:
    scn = _scn(
        steps=[
            {
                "actor": "vic-jump",
                "description": "post-auth recon",
                "command": "whoami",
                "via": "ssh",
                "from": "atk-kali",
                "as_user": "admin",
            }
        ]
    )
    ex = FakeExec()
    run_plan(scn, execute=ex, sleep=lambda _s: None)

    argv = ex.calls[0][0]
    # executed FROM atk-kali (docker exec atk-kali ...), reaching vic-jump over ssh as admin
    assert argv[:3] == ["docker", "exec", "atk-kali"]
    joined = " ".join(argv)
    assert "ssh" in joined
    assert "admin@vic-jump" in joined
    assert "whoami" in joined


def test_expect_failure_inverts_success() -> None:
    scn = _scn(
        steps=[
            {
                "actor": "atk-kali",
                "description": "must fail",
                "command": "false",
                "expect_failure": True,
            }
        ]
    )
    results = run_plan(scn, execute=FakeExec(rc=1), sleep=lambda _s: None)
    assert results[0].returncode == 1
    assert results[0].ok is True  # non-zero is success when expect_failure


def test_setup_actions_run_before_steps() -> None:
    scn = _scn(
        setup=[{"actor": "vic-jump", "command": "useradd admin", "description": "seed"}],
        steps=[{"actor": "atk-kali", "description": "go", "command": "echo go"}],
    )
    ex = FakeExec()
    run_plan(scn, execute=ex, sleep=lambda _s: None)

    assert "useradd admin" in ex.calls[0][0][-1]  # setup first
    assert "echo go" in ex.calls[1][0][-1]  # then steps
