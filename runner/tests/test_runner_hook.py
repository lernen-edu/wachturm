"""run_plan must expose a seam between setup and steps.

The CLI snapshots the Wazuh alerts.json offset AFTER setup (useradd
etc.) but BEFORE the attack steps, so setup-generated noise can't
contaminate the expected_alerts integrity window (advisor #4). That
requires a hook fired exactly once, after the last setup action and
before the first step.
"""

from wachturm.runner import run_plan
from wachturm.scenario import Scenario

BASE = {
    "schema_version": "1.0",
    "id": "SCN-902",
    "name": "hook fixture",
    "description": "between-setup-and-steps hook",
    "author": "Wachturm Contributors",
    "created": "2026-05-16",
    "difficulty": "easy",
    "category": "discovery",
    "expected_verdict": "benign",
    "duration_minutes": 1,
    "expected_alerts": [],
    "answer_key": {"verdict": "benign", "severity": "low", "confidence": "low"},
}


def test_between_hook_fires_after_setup_before_steps() -> None:
    scn = Scenario.model_validate(
        {
            **BASE,
            "setup": [{"actor": "vic-jump", "command": "useradd admin", "description": "seed"}],
            "steps": [{"actor": "atk-kali", "description": "go", "command": "echo go"}],
        }
    )
    order: list[str] = []

    def execute(argv: list[str], _timeout: int) -> tuple[int, str, str]:
        order.append("setup" if "useradd admin" in argv[-1] else "step")
        return (0, "", "")

    def between() -> None:
        order.append("between")

    run_plan(scn, execute=execute, sleep=lambda _s: None, between_setup_and_steps=between)

    assert order == ["setup", "between", "step"]


def test_between_hook_optional_and_defaults_off() -> None:
    scn = Scenario.model_validate(
        {**BASE, "steps": [{"actor": "atk-kali", "description": "go", "command": "echo go"}]}
    )
    # No hook passed -> no error, steps still run.
    res = run_plan(scn, execute=lambda _a, _t: (0, "", ""), sleep=lambda _s: None)
    assert len(res) == 1
