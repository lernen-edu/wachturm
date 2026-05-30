"""TDD for wachturm.hints (P3a-3a).

The hint system shares state with scoring: each revealed hint costs the
student 5 points (SCENARIO_SCHEMA §7, default). Split like the rest of
the runner: a PURE model (``HintState``/``next_hint``/``hint_penalty``,
unit-tested here) plus a thin file IO boundary
(``~/.wachturm/hints/<SCN>.json``, base dir injected for tests).
"""

from pathlib import Path

from wachturm.hints import (
    HintState,
    hint_penalty,
    load_state,
    next_hint,
    save_state,
)

# ── pure model ───────────────────────────────────────────────────────


def test_reveal_advances_and_caps_at_list_end() -> None:
    hints = ["a", "b", "c"]
    text, st1 = next_hint(hints, HintState("SCN-001", 0))
    assert text == "a" and st1.revealed == 1
    text, st2 = next_hint(hints, st1)
    assert text == "b" and st2.revealed == 2
    text, st3 = next_hint(hints, HintState("SCN-001", 3))
    assert text is None and st3.revealed == 3  # exhausted, no over-count


def test_next_hint_on_empty_list_returns_none() -> None:
    text, st = next_hint([], HintState("SCN-009", 0))
    assert text is None and st.revealed == 0


def test_penalty_is_five_per_revealed() -> None:
    assert hint_penalty(HintState("SCN-001", 0)) == 0.0
    assert hint_penalty(HintState("SCN-001", 2)) == 10.0
    assert hint_penalty(HintState("SCN-001", 4)) == 20.0


# ── file IO boundary (base dir injected) ─────────────────────────────


def test_load_missing_is_zero(tmp_path: Path) -> None:
    st = load_state("SCN-001", base=tmp_path)
    assert st == HintState("SCN-001", 0)


def test_save_then_load_roundtrips(tmp_path: Path) -> None:
    save_state(HintState("SCN-001", 2), base=tmp_path)
    assert load_state("SCN-001", base=tmp_path).revealed == 2


def test_corrupt_state_file_degrades_to_zero(tmp_path: Path) -> None:
    (tmp_path / "SCN-001.json").write_text("{ not json", encoding="utf-8")
    assert load_state("SCN-001", base=tmp_path) == HintState("SCN-001", 0)


def test_saved_file_is_0600_under_0700_dir(tmp_path: Path) -> None:
    save_state(HintState("SCN-007", 1), base=tmp_path / "hints")
    f = tmp_path / "hints" / "SCN-007.json"
    assert f.is_file()
    assert (f.stat().st_mode & 0o777) == 0o600
    assert ((tmp_path / "hints").stat().st_mode & 0o777) == 0o700
