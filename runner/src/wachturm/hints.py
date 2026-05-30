"""Hint reveal + cost model (P3a-3a).

``make hint SCN=NNN`` reveals the next un-revealed hint from the
scenario YAML and costs the student points (SCENARIO_SCHEMA §7 — 5 per
hint, default). Scoring must see the same count, so revealed-hint state
is persisted to a loopback file (``~/.wachturm/hints/<SCN>.json``, same
convention as the IRIS/Cortex tokens) that both ``wachturm hint`` writes
and ``wachturm score`` reads. Closes the "hint-farm a perfect score"
risk: every reveal is a -5 ``hint_penalty`` component.

Split like the rest of the runner: a PURE model (``HintState`` /
``next_hint`` / ``hint_penalty``) and a thin, corrupt-safe file IO
boundary with an injectable base dir (tests pass ``base=tmp_path``;
the CLI uses :func:`default_base`, honouring ``WACHTURM_HINT_DIR``).
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

_PENALTY_PER_HINT = 5.0
_ENV_DIR = "WACHTURM_HINT_DIR"


@dataclass(frozen=True)
class HintState:
    """How many of a scenario's hints the student has revealed."""

    scenario_id: str
    revealed: int


def next_hint(hints: list[str], state: HintState) -> tuple[str | None, HintState]:
    """Reveal the next hint.

    Returns ``(text, advanced_state)`` or, when every hint is already
    revealed (or there are none), ``(None, unchanged_state)`` — the
    count never advances past ``len(hints)`` so it can't over-penalise.
    """
    if state.revealed >= len(hints):
        return None, state
    return hints[state.revealed], HintState(state.scenario_id, state.revealed + 1)


def hint_penalty(state: HintState) -> float:
    """Points to subtract for the hints revealed so far (5 each)."""
    return _PENALTY_PER_HINT * state.revealed


def default_base() -> Path:
    """Hint-state dir: ``$WACHTURM_HINT_DIR`` or ``~/.wachturm/hints``."""
    env = os.environ.get(_ENV_DIR)
    return Path(env) if env else Path.home() / ".wachturm" / "hints"


def load_state(scenario_id: str, *, base: Path | None = None) -> HintState:
    """Read persisted hint state. Missing or corrupt → zeroed (the
    scorer must never crash because a hint file is malformed)."""
    base = base if base is not None else default_base()
    path = base / f"{scenario_id}.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        revealed = int(raw["revealed"])
        return HintState(scenario_id, max(0, revealed))
    except (OSError, ValueError, KeyError, TypeError):
        return HintState(scenario_id, 0)


def save_state(state: HintState, *, base: Path | None = None) -> None:
    """Persist hint state atomically: dir 0700, file 0600 (loopback-only
    dev convenience, identical to the token files)."""
    base = base if base is not None else default_base()
    base.mkdir(parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    path = base / f"{state.scenario_id}.json"
    payload = json.dumps({"scenario_id": state.scenario_id, "revealed": state.revealed})
    fd, tmp = tempfile.mkstemp(prefix=f".{state.scenario_id}-", dir=base)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
