"""TDD for wachturm.scoring (P2-M5).

The scorer splits like M1/M3: a PURE ``score()`` over a normalized
``CaseSnapshot`` (fully unit-tested here, no lab) plus a thin injected
IRIS fetch (grounded, e2e-verified by ``make score``). The rubric is
SCENARIO_SCHEMA.md §6 (verdict 50, severity 15, confidence 5,
observables 15, summary_keywords 10, enrichment 5; severity/confidence
credited within ±1 step; weights overridable per scenario).
"""

import httpx

from wachturm.scenario import AnswerKey, KeywordGroup, Observable, RequiredEnrichment
from wachturm.scoring import (
    CaseSnapshot,
    ScoreResult,
    component,
    fetch_latest_closed_case,
    score,
)


def _ak(**over: object) -> AnswerKey:
    base: dict[str, object] = {
        "verdict": "true_positive",
        "severity": "high",
        "confidence": "high",
        "required_observables": [
            Observable(type="ip", value="10.50.10.250", role="source"),
            Observable(type="hostname", value="vic-jump", role="target"),
        ],
        "required_enrichment": [],
        "summary_keywords": [
            KeywordGroup(any_of=["brute force", "brute-force"]),
            KeywordGroup(any_of=["compromise", "successful login"]),
        ],
        "next_steps": [],
        "reasoning": "Textbook credential brute-force compromise.",
    }
    base.update(over)
    return AnswerKey.model_validate(base)


def _snap(**over: object) -> CaseSnapshot:
    base: dict[str, object] = {
        "case_id": 7,
        "closed": True,
        "verdict": "true_positive",
        "severity": "high",
        "confidence": "high",
        "ioc_values": frozenset({"10.50.10.250", "vic-jump", "admin"}),
        "summary_text": "Sustained brute force from 10.50.10.250 then a successful login.",
    }
    base.update(over)
    return CaseSnapshot(**base)  # type: ignore[arg-type]


def _comp(res: ScoreResult, name: str) -> float:
    return component(res, name).awarded


# ── perfect case ─────────────────────────────────────────────────────


def test_perfect_case_scores_full() -> None:
    res = score(_snap(), _ak(), scenario_id="SCN-001")
    assert res.total == 100.0
    assert res.possible == 100.0
    assert res.graded_case_id == 7
    assert "brute-force" in res.reasoning.lower()


# ── verdict (50) ─────────────────────────────────────────────────────


def test_wrong_verdict_loses_fifty() -> None:
    res = score(_snap(verdict="false_positive"), _ak())
    assert _comp(res, "verdict") == 0.0
    assert res.total == 50.0  # everything else still correct


def test_missing_verdict_tag_loses_fifty() -> None:
    res = score(_snap(verdict=None), _ak())
    assert _comp(res, "verdict") == 0.0


# ── severity / confidence (±1 step) ──────────────────────────────────


def test_severity_within_one_step_credited() -> None:
    # expected high; student medium = one step => credited
    assert _comp(score(_snap(severity="medium"), _ak()), "severity") == 15.0


def test_severity_two_steps_off_not_credited() -> None:
    # expected high; student low = two steps => not credited
    assert _comp(score(_snap(severity="low"), _ak()), "severity") == 0.0


def test_confidence_one_step_credited_two_not() -> None:
    assert _comp(score(_snap(confidence="medium"), _ak()), "confidence") == 5.0
    assert _comp(score(_snap(confidence="low"), _ak()), "confidence") == 0.0


# ── observables (15) ─────────────────────────────────────────────────


def test_all_required_observables_present() -> None:
    assert _comp(score(_snap(), _ak()), "observables") == 15.0


def test_missing_one_required_observable_loses_fifteen() -> None:
    res = score(_snap(ioc_values=frozenset({"10.50.10.250"})), _ak())  # vic-jump missing
    c = component(res, "observables")
    assert c.awarded == 0.0
    assert "vic-jump" in c.detail


# ── summary_keywords (10) ────────────────────────────────────────────


def test_one_keyword_group_match_is_enough() -> None:
    # only the first group's phrase present
    res = score(_snap(summary_text="this was a brute force attempt"), _ak())
    assert _comp(res, "summary_keywords") == 10.0


def test_no_keyword_match_loses_ten() -> None:
    res = score(_snap(summary_text="nothing relevant here"), _ak())
    assert _comp(res, "summary_keywords") == 0.0


# ── enrichment (5) vacuous ───────────────────────────────────────────


def test_enrichment_vacuously_satisfied_when_none_required() -> None:
    res = score(_snap(), _ak(required_enrichment=[]))
    c = component(res, "enrichment")
    assert c.awarded == 5.0
    assert "vacuous" in c.detail.lower()


def test_enrichment_required_not_evidenced_loses_five() -> None:
    ak = _ak(
        required_enrichment=[
            RequiredEnrichment(observable_type="ip", analyzer="AbuseIPDB", required=True)
        ]
    )
    res = score(_snap(summary_text="no enrichment mentioned"), ak)
    assert _comp(res, "enrichment") == 0.0


# ── graceful: no case / not closed ───────────────────────────────────


def test_no_case_is_graceful_zero_with_reasoning() -> None:
    res = score(None, _ak(), scenario_id="SCN-001")
    assert res.total == 0.0
    assert res.graded_case_id is None
    assert "no case" in res.reasoning.lower()


def test_unclosed_case_is_graceful_zero_with_reasoning() -> None:
    res = score(_snap(closed=False, case_id=12), _ak())
    assert res.total == 0.0
    assert res.graded_case_id == 12
    assert "clos" in res.reasoning.lower()


# ── configurable weights (schema §6: "configurable in scoring_weights") ─


def test_scenario_weight_override_changes_max_and_award() -> None:
    res = score(_snap(), _ak(), weights={"verdict": 70.0, "summary_keywords": 0.0})
    assert _comp(res, "verdict") == 70.0
    assert component(res, "summary_keywords").possible == 0.0
    # 70 + 15 + 5 + 15 + 0 + 5
    assert res.possible == 110.0
    assert res.total == 110.0


# ── hint penalty (schema §7: each revealed hint costs 5) ─────────────


def test_hint_penalty_subtracts_five_per_hint() -> None:
    res = score(_snap(), _ak(), scenario_id="SCN-001", hints_used=2)
    assert component(res, "hint_penalty").awarded == -10.0
    assert component(res, "hint_penalty").possible == 0.0
    assert res.total == 90.0  # 100 - 10
    assert res.possible == 100.0  # penalty does not change the max


def test_zero_hints_used_still_emits_a_zeroed_component() -> None:
    res = score(_snap(), _ak(), hints_used=0)
    assert component(res, "hint_penalty").awarded == 0.0
    assert res.total == 100.0


def test_hint_penalty_cannot_drive_total_negative() -> None:
    res = score(_snap(verdict="false_positive"), _ak(), hints_used=99)
    assert res.total == 0.0


# ── fetch_latest_closed_case (injected IRIS boundary) ────────────────


def _iris(handler: object) -> httpx.Client:
    return httpx.Client(
        base_url="https://iris-nginx:8443",
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
    )


def _ok(data: object) -> httpx.Response:
    return httpx.Response(200, json={"status": "success", "data": data})


def test_fetch_picks_newest_closed_and_parses_tags_iocs_summary() -> None:
    def h(req: httpx.Request) -> httpx.Response:
        p = req.url.path
        if p == "/manage/cases/list":
            return _ok(
                [
                    {"case_id": 5, "state_id": 9},  # older closed
                    {"case_id": 9, "state_id": 9},  # newest closed -> graded
                    {"case_id": 11, "state_id": 3},  # newer but open -> ignored
                ]
            )
        if p == "/manage/cases/9":
            return _ok(
                {
                    "case_id": 9,
                    "case_tags": "scenario:SCN-001,verdict:true_positive,"
                    "severity:high,confidence:high",
                    "case_description": "Brute force from 10.50.10.250 then success.",
                }
            )
        if p == "/case/ioc/list":
            assert req.url.params.get("cid") == "9"
            return _ok({"ioc": [{"ioc_value": "10.50.10.250"}, {"ioc_value": "vic-jump"}]})
        raise AssertionError(f"unexpected {p}")

    snap = fetch_latest_closed_case(_iris(h))
    assert snap is not None
    assert snap.case_id == 9 and snap.closed is True
    assert snap.verdict == "true_positive"
    assert snap.severity == "high"
    assert snap.confidence == "high"
    assert snap.ioc_values == frozenset({"10.50.10.250", "vic-jump"})
    assert "brute force" in snap.summary_text.lower()


def test_fetch_returns_none_when_no_cases() -> None:
    assert fetch_latest_closed_case(_iris(lambda r: _ok([]))) is None


def test_fetch_unclosed_when_cases_exist_but_none_closed() -> None:
    def h(req: httpx.Request) -> httpx.Response:
        return _ok([{"case_id": 3, "state_id": 3}, {"case_id": 7, "state_id": 2}])

    snap = fetch_latest_closed_case(_iris(h))
    assert snap is not None
    assert snap.closed is False
    assert snap.case_id == 7  # newest, so the message names a real case


def test_fetch_degrades_to_none_on_http_error() -> None:
    snap = fetch_latest_closed_case(_iris(lambda r: httpx.Response(500, text="boom")))
    assert snap is None


def test_fetch_normalises_disposition_tag_case_and_whitespace() -> None:
    # A student typing "verdict: True_Positive" in the IRIS UI must not
    # silently lose 50 points to capitalisation/spacing.
    def h(req: httpx.Request) -> httpx.Response:
        p = req.url.path
        if p == "/manage/cases/list":
            return _ok([{"case_id": 8, "state_id": 9}])
        if p == "/manage/cases/8":
            return _ok(
                {
                    "case_id": 8,
                    "case_tags": "verdict: True_Positive, severity:HIGH ,confidence: High",
                    "case_description": "x",
                }
            )
        return _ok({"ioc": []})

    snap = fetch_latest_closed_case(_iris(h))
    assert snap is not None
    assert snap.verdict == "true_positive"
    assert snap.severity == "high"
    assert snap.confidence == "high"


def test_fetch_tolerates_missing_disposition_tags() -> None:
    def h(req: httpx.Request) -> httpx.Response:
        p = req.url.path
        if p == "/manage/cases/list":
            return _ok([{"case_id": 4, "state_id": 9}])
        if p == "/manage/cases/4":
            return _ok({"case_id": 4, "case_tags": "scenario:SCN-002", "case_description": "x"})
        return _ok({"ioc": []})

    snap = fetch_latest_closed_case(_iris(h))
    assert snap is not None
    assert snap.verdict is None and snap.severity is None and snap.confidence is None
    assert snap.ioc_values == frozenset()
