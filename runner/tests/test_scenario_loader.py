"""Tests for ``load_scenario`` — the file loader used by the CLI/runner.

``wachturm scenario validate`` and ``make scenario`` both load a YAML
path; they need a single entry point that returns a validated
``Scenario`` or raises one clear, CLI-friendly error (not a raw YAML or
Pydantic traceback).
"""

import textwrap
from pathlib import Path

import pytest

from wachturm.scenario import ScenarioError, load_scenario

VALID = textwrap.dedent("""
    schema_version: "1.0"
    id: SCN-077
    name: "Loader fixture"
    description: "Minimal valid scenario for loader tests."
    author: "Wachturm Contributors"
    created: 2026-05-16
    difficulty: easy
    category: discovery
    expected_verdict: benign
    duration_minutes: 1
    steps:
      - actor: atk-kali
        description: "noop"
        command: "true"
    expected_alerts: []
    answer_key:
      verdict: benign
      severity: low
      confidence: low
    """)


def test_load_scenario_reads_valid_file(tmp_path: Path) -> None:
    p = tmp_path / "SCN-077-x.yml"
    p.write_text(VALID)
    scn = load_scenario(p)
    assert scn.id == "SCN-077"
    assert scn.expected_verdict == "benign"


def test_load_scenario_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ScenarioError, match="not found"):
        load_scenario(tmp_path / "nope.yml")


def test_load_scenario_malformed_yaml_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.yml"
    p.write_text("id: SCN-001\n  : : not yaml :::\n")
    with pytest.raises(ScenarioError, match="YAML"):
        load_scenario(p)


def test_load_scenario_schema_violation_raises_clear_error(tmp_path: Path) -> None:
    p = tmp_path / "SCN-078-x.yml"
    p.write_text(VALID.replace("id: SCN-077", "id: BADID"))
    with pytest.raises(ScenarioError, match="SCN-078-x.yml"):
        load_scenario(p)
