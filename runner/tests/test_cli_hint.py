"""TDD for `wachturm hint` (P3a-3a.4).

`make hint SCN=NNN` reveals the next un-revealed YAML hint and persists
the count to ``$WACHTURM_HINT_DIR/<SCN>.json`` so ``score`` deducts 5
per hint. Thin glue over :mod:`wachturm.hints`; the e2e wiring is
verified by ``make hint`` against the lab.
"""

from pathlib import Path

from typer.testing import CliRunner

from wachturm.cli import app

_runner = CliRunner()


def _hint(scn: str, hint_dir: Path) -> str:
    res = _runner.invoke(app, ["hint", scn], env={"WACHTURM_HINT_DIR": str(hint_dir)})
    assert res.exit_code == 0, res.output
    return res.output


def test_hint_reveals_progressively_and_then_stops(tmp_path: Path) -> None:
    # SCN-001 ships exactly 3 hints (general -> specific).
    out1 = _hint("SCN-001", tmp_path)
    assert "Look at the source IP" in out1
    assert "1 of 3" in out1 and "-5" in out1  # progress + cost shown

    out2 = _hint("SCN-001", tmp_path)
    assert "Walk the alert cluster" in out2
    assert "2 of 3" in out2

    out3 = _hint("SCN-001", tmp_path)
    assert "Pivot to what happened" in out3
    assert "3 of 3" in out3

    out4 = _hint("SCN-001", tmp_path)
    assert "no more hints" in out4.lower()


def test_hint_state_persists_to_the_injected_dir(tmp_path: Path) -> None:
    _hint("SCN-001", tmp_path)
    _hint("SCN-001", tmp_path)
    assert (tmp_path / "SCN-001.json").is_file()
    from wachturm.hints import load_state

    assert load_state("SCN-001", base=tmp_path).revealed == 2


def test_hint_unknown_scenario_errors_cleanly(tmp_path: Path) -> None:
    res = _runner.invoke(app, ["hint", "SCN-999"], env={"WACHTURM_HINT_DIR": str(tmp_path)})
    assert res.exit_code == 1
