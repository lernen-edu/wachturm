"""CI enforcement: every scenario is a complete, no-spoiler trio (P3a-0.3).

BUILD_ORDER §3a DoD: "CI enforces the three-file requirement per
scenario." This test is that enforcement (CI runs ``pytest``). It also
enforces the 2026-05-17 no-spoiler-name rule via
``wachturm.scenario_lint`` over every scenario's student-facing strings.

A failure here means a scenario is missing a file, doesn't parse, or
its name/description/brief-title gives the verdict away — fix the
scenario, never this test.
"""

from pathlib import Path

import pytest

from wachturm.scenario import load_scenario
from wachturm.scenario_lint import find_spoilers

_SCENARIOS = Path(__file__).resolve().parents[2] / "scenarios"
_YAMLS = sorted(_SCENARIOS.glob("SCN-*.yml"))


def test_scenarios_directory_is_populated() -> None:
    assert _YAMLS, f"no SCN-*.yml found under {_SCENARIOS}"


@pytest.mark.parametrize("yml", _YAMLS, ids=lambda p: p.stem)
def test_each_scenario_has_brief_and_instructor_siblings(yml: Path) -> None:
    stem = yml.name[:-4]  # drop ".yml"
    brief = _SCENARIOS / f"{stem}.brief.md"
    instructor = _SCENARIOS / f"{stem}.instructor.md"
    assert brief.is_file(), f"missing {brief.name} for {yml.name}"
    assert instructor.is_file(), f"missing {instructor.name} for {yml.name}"


@pytest.mark.parametrize("yml", _YAMLS, ids=lambda p: p.stem)
def test_each_scenario_yaml_parses(yml: Path) -> None:
    load_scenario(yml)  # raises ScenarioError on a bad spec


def _brief_title(stem: str) -> str:
    text = (_SCENARIOS / f"{stem}.brief.md").read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("# "):
            return line
    return ""


@pytest.mark.parametrize("yml", _YAMLS, ids=lambda p: p.stem)
def test_no_spoiler_in_name_description_or_brief_title(yml: Path) -> None:
    spec = load_scenario(yml)
    name_hits = find_spoilers(spec.name)
    desc_hits = find_spoilers(spec.description)
    title_hits = find_spoilers(_brief_title(yml.name[:-4]))
    assert not name_hits, f"{yml.name} name reveals the verdict: {name_hits}"
    assert not desc_hits, f"{yml.name} description reveals the verdict: {desc_hits}"
    assert not title_hits, f"{yml.name} brief title reveals the verdict: {title_hits}"
