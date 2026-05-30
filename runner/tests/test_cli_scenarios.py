"""TDD for `wachturm scenarios` (P3a-WS2).

`make scenarios` must list the library with id / difficulty / verdict /
category and filter by --difficulty, --verdict, --category (BUILD_ORDER
§3a DoD). Thin glue over wachturm.scenario.load_scenario; reads the
real scenarios/ trio (15 at v1.0).
"""

from typer.testing import CliRunner

from wachturm.cli import app

_runner = CliRunner()


def _run(*args: str) -> str:
    res = _runner.invoke(app, ["scenarios", *args])
    assert res.exit_code == 0, res.output
    return res.output


def test_lists_all_15_with_columns_and_count() -> None:
    out = _run()
    for scn in ("SCN-001", "SCN-010", "SCN-021", "SCN-034"):
        assert scn in out
    assert "true_positive" in out and "false_positive" in out and "benign" in out
    assert "15 scenario(s)" in out


def test_filter_by_verdict() -> None:
    out = _run("--verdict", "false_positive")
    assert "5 scenario(s)" in out
    assert "true_positive" not in out
    assert "SCN-002" in out  # a known FP


def test_filter_by_difficulty() -> None:
    out = _run("--difficulty", "hard")
    assert "2 scenario(s)" in out
    assert "SCN-021" in out and "SCN-023" in out
    assert "SCN-001" not in out


def test_filter_by_difficulty_accepts_student_facing_synonyms() -> None:
    # The whole curriculum teaches Beginner/Medium/Advanced; the CLI stores
    # easy/medium/hard. `make scenarios FILTER='--difficulty beginner'` must
    # NOT return a silent empty list — accept the taught words (and any
    # capitalization) by mapping them onto the schema vocabulary.
    easy = _run("--difficulty", "easy")
    assert "8 scenario(s)" in easy
    assert _run("--difficulty", "beginner") == easy
    assert _run("--difficulty", "Beginner") == easy
    advanced = _run("--difficulty", "advanced")
    assert "2 scenario(s)" in advanced
    assert "SCN-021" in advanced and "SCN-023" in advanced


def test_filter_by_category_substring() -> None:
    out = _run("--category", "benign")  # benign_admin / benign_user
    assert "SCN-003" in out  # benign_user
    assert "true_positive" not in out


def test_output_is_sorted_by_id() -> None:
    out = _run()
    ids = [ln.split()[0] for ln in out.splitlines() if ln.startswith("SCN-")]
    assert ids == sorted(ids)


def test_unknown_filter_yields_zero_not_error() -> None:
    out = _run("--difficulty", "nonexistent")
    assert "0 scenario(s)" in out


def test_step_progress_line_omits_spoiler_description() -> None:
    # `make scenario` must NOT echo a step's author-written description.
    # Those describe the actual attack (e.g. SCN-002's "authenticated scan
    # ... all fail"), which would hand the student the verdict they are
    # supposed to derive. The progress line is structural — index/total +
    # rc + ✓/✗ — and the helper has no parameter a description could leak
    # through. Regression guard for the no-spoiler design (WS0).
    from wachturm.cli import _step_progress

    line = _step_progress(2, 3, 0, True)
    assert "step 2/3" in line and "rc=0" in line and "✓" in line
    assert _step_progress(2, 3, 1, False).startswith("  ✗")
