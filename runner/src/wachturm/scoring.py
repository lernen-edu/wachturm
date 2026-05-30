"""Score a student's triaged IRIS case against a scenario answer key (P2-M5).

Rubric — SCENARIO_SCHEMA.md §6 (weights overridable per scenario via
``scoring_weights``):

    verdict 50 | severity 15 | confidence 5 | observables 15 |
    summary_keywords 10 | enrichment 5

Severity and confidence are credited when the student is within ±1 step
of the answer key (a calibration tolerance, per §6). "At least one
``summary_keywords`` ``any_of`` group matched" earns the full keyword
weight. Enrichment is **vacuously satisfied** when the answer key has no
``required: true`` entry — true for all three Phase-2 scenarios — and
that 5 is awarded rather than renormalised, so the printed weights stay
equal to the documented rubric (the documented-pivot model: enrichment
is asked but not graded unless a scenario marks it required).

This module is split like the M1/M3 integrations: a PURE ``score()``
over a normalised :class:`CaseSnapshot` (unit-tested with no lab) and a
thin injected IRIS fetch (grounded, e2e-verified by ``make score``).
IRIS v2.4.20's case JSON API (``get_case_details_rt``) deliberately
omits ``severity_id`` and ``closing_note`` (verified live), so M5 uses
a **uniform ``case_tags`` convention for all three dispositions** —
``verdict:<v>``, ``severity:<s>``, ``confidence:<c>`` — and matches the
summary keywords against the case Description (the IRIS "Summary"
field, which the API does return); observables are the case IOCs. The
graded case is the most-recently-*closed* one — closing a case is the
student's "this is my submission" signal.
"""

from dataclasses import dataclass, field
from typing import Any

import httpx

from wachturm.hints import HintState, hint_penalty
from wachturm.scenario import AnswerKey

DEFAULT_WEIGHTS: dict[str, float] = {
    "verdict": 50.0,
    "severity": 15.0,
    "confidence": 5.0,
    "observables": 15.0,
    "summary_keywords": 10.0,
    "enrichment": 5.0,
}

_SEVERITY_ORDER = ("low", "medium", "high", "critical")
_CONFIDENCE_ORDER = ("low", "medium", "high")


@dataclass(frozen=True)
class ScoreComponent:
    """One rubric line's outcome."""

    name: str
    awarded: float
    possible: float
    detail: str


@dataclass(frozen=True)
class CaseSnapshot:
    """A normalised view of the student's IRIS case (the fetch boundary
    produces this; ``score`` is pure over it)."""

    case_id: int | None
    closed: bool
    verdict: str | None
    severity: str | None
    confidence: str | None
    ioc_values: frozenset[str]
    summary_text: str


@dataclass(frozen=True)
class ScoreResult:
    """The structured score ``make score`` prints."""

    scenario_id: str
    graded_case_id: int | None
    total: float
    possible: float
    components: list[ScoreComponent] = field(default_factory=list)
    reasoning: str = ""


def component(result: ScoreResult, name: str) -> ScoreComponent:
    """Return the named component (raises KeyError-like if absent)."""
    for c in result.components:
        if c.name == name:
            return c
    raise KeyError(name)


def _within_one_step(student: str | None, expected: str, order: tuple[str, ...]) -> bool:
    if student is None:
        return False
    try:
        return abs(order.index(student) - order.index(expected)) <= 1
    except ValueError:
        return False


def score(
    snapshot: CaseSnapshot | None,
    answer_key: AnswerKey,
    *,
    scenario_id: str = "",
    weights: dict[str, float] | None = None,
    hints_used: int = 0,
) -> ScoreResult:
    """Score ``snapshot`` against ``answer_key``. Never raises.

    A missing case or an unclosed case yields a zeroed result with an
    actionable ``reasoning`` rather than an error (DoD). ``hints_used``
    (revealed hints, from :mod:`wachturm.hints`) adds a negative
    ``hint_penalty`` component of -5 each (SCENARIO_SCHEMA §7); it never
    changes ``possible`` and the printed ``total`` is floored at 0.
    """
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    possible_total = sum(w.values())

    if snapshot is None or snapshot.case_id is None:
        return ScoreResult(
            scenario_id,
            None,
            0.0,
            possible_total,
            [],
            "No case found in IRIS to grade. Triage the scenario in IRIS — set the "
            "verdict:/severity:/confidence: case tags, write your conclusion in the "
            "case Summary — then CLOSE the case and re-run `make score`.",
        )
    if not snapshot.closed:
        return ScoreResult(
            scenario_id,
            snapshot.case_id,
            0.0,
            possible_total,
            [],
            f"Case #{snapshot.case_id} is still open. `make score` grades the most "
            "recently closed case — close exactly the case you triaged, then re-run.",
        )

    comps: list[ScoreComponent] = []

    v_ok = snapshot.verdict is not None and snapshot.verdict == answer_key.verdict
    comps.append(
        ScoreComponent(
            "verdict",
            w["verdict"] if v_ok else 0.0,
            w["verdict"],
            f"tag verdict={snapshot.verdict!r}, expected {answer_key.verdict!r}",
        )
    )

    s_ok = _within_one_step(snapshot.severity, answer_key.severity, _SEVERITY_ORDER)
    comps.append(
        ScoreComponent(
            "severity",
            w["severity"] if s_ok else 0.0,
            w["severity"],
            f"{snapshot.severity!r} vs {answer_key.severity!r} (±1 step credited)",
        )
    )

    c_ok = _within_one_step(snapshot.confidence, answer_key.confidence, _CONFIDENCE_ORDER)
    comps.append(
        ScoreComponent(
            "confidence",
            w["confidence"] if c_ok else 0.0,
            w["confidence"],
            f"{snapshot.confidence!r} vs {answer_key.confidence!r} (±1 step credited)",
        )
    )

    required = [o.value for o in answer_key.required_observables]
    missing = [v for v in required if v not in snapshot.ioc_values]
    comps.append(
        ScoreComponent(
            "observables",
            w["observables"] if not missing else 0.0,
            w["observables"],
            "all required IOCs present" if not missing else f"missing {missing}",
        )
    )

    text = snapshot.summary_text.lower()
    groups = answer_key.summary_keywords
    kw_ok = (not groups) or any(any(kw.lower() in text for kw in g.any_of) for g in groups)
    comps.append(
        ScoreComponent(
            "summary_keywords",
            w["summary_keywords"] if kw_ok else 0.0,
            w["summary_keywords"],
            "≥1 any_of group matched" if kw_ok else "no any_of group matched in summary",
        )
    )

    required_enr = [e for e in answer_key.required_enrichment if e.required]
    if not required_enr:
        e_ok, e_detail = True, "vacuously satisfied (no required:true enrichment in answer key)"
    else:
        unmet = [e.analyzer for e in required_enr if e.analyzer.lower() not in text]
        e_ok = not unmet
        e_detail = (
            "required enrichment evidenced in summary"
            if e_ok
            else f"no evidence of required enrichment {unmet} in the closing note"
        )
    comps.append(
        ScoreComponent("enrichment", w["enrichment"] if e_ok else 0.0, w["enrichment"], e_detail)
    )

    penalty = hint_penalty(HintState(scenario_id, hints_used))
    comps.append(
        ScoreComponent(
            "hint_penalty",
            -penalty,
            0.0,
            f"{hints_used} hint(s) revealed (-5 each)" if hints_used else "no hints revealed",
        )
    )

    total = max(0.0, sum(c.awarded for c in comps))
    return ScoreResult(
        scenario_id,
        snapshot.case_id,
        total,
        possible_total,
        comps,
        answer_key.reasoning.strip(),
    )


# ── IRIS fetch boundary (grounded; e2e-verified by `make score`) ─────
#
# IRIS v2.4.20's case JSON API (`get_case_details_rt`) deliberately
# omits severity_id and closing_note, so M5 reads only the fields it
# DOES return: a uniform ``case_tags`` convention carries
# verdict/severity/confidence, and the student's assessment lives in
# the case Description (the IRIS "Summary" field) where the
# summary_keywords are matched. The graded case is the newest *closed*
# one — closing a case is the student's "submit" signal. Every HTTP
# failure degrades to None so `make score` never crashes (DoD).

_CLOSED_STATE_ID = 9  # IRIS case-states: 9 = Closed (grounded live)


def _tags_to_map(case_tags: str | None) -> dict[str, str]:
    """``"verdict:true_positive,severity:high"`` -> a {k: v} map."""
    out: dict[str, str] = {}
    for chunk in (case_tags or "").split(","):
        if ":" in chunk:
            k, _, v = chunk.partition(":")
            out[k.strip().lower()] = v.strip()
    return out


def _data(resp: httpx.Response) -> Any:
    if resp.status_code != 200:
        raise httpx.HTTPError(f"HTTP {resp.status_code}")
    body = resp.json()
    return body.get("data") if isinstance(body, dict) else None


def fetch_latest_closed_case(client: httpx.Client) -> CaseSnapshot | None:
    """Snapshot the newest closed IRIS case.

    Returns ``None`` when no case exists at all; a snapshot with
    ``closed=False`` (naming the newest case) when cases exist but none
    are closed, so ``score`` can tell the student to close the one they
    triaged.
    """
    try:
        cases = _data(client.get("/manage/cases/list")) or []
        if not isinstance(cases, list) or not cases:
            return None
        closed = [c for c in cases if c.get("state_id") == _CLOSED_STATE_ID]
        if not closed:
            newest = max(cases, key=lambda c: c.get("case_id", 0))
            return CaseSnapshot(newest.get("case_id"), False, None, None, None, frozenset(), "")
        case = max(closed, key=lambda c: c.get("case_id", 0))
        cid = case.get("case_id")
        detail = _data(client.get(f"/manage/cases/{cid}")) or {}
        tags = _tags_to_map(detail.get("case_tags"))
        iocs = _data(client.get("/case/ioc/list", params={"cid": cid})) or {}
        ioc_values = frozenset(
            i.get("ioc_value", "") for i in (iocs.get("ioc") or []) if i.get("ioc_value")
        )

        # verdict/severity/confidence are a controlled vocabulary, so
        # normalise case ("True_Positive" -> "true_positive"): a student
        # must not lose points to capitalisation. IOC values are NOT
        # lowercased (hostnames/hashes can be case-significant).
        def _norm(key: str) -> str | None:
            v = tags.get(key)
            return v.lower() if v else None

        return CaseSnapshot(
            case_id=cid,
            closed=True,
            verdict=_norm("verdict"),
            severity=_norm("severity"),
            confidence=_norm("confidence"),
            ioc_values=ioc_values,
            summary_text=str(detail.get("case_description") or ""),
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None
