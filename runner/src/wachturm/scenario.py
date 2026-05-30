"""Canonical implementation of the Wachturm scenario schema (v1.0).

Per ``SCENARIO_SCHEMA.md`` §10 these Pydantic models — not the prose —
are the canonical schema. If the doc and these models disagree, the
models win and the doc gets a PR. Field names and constraints track the
locked schema §2–§9.

Deliberately no ``from __future__ import annotations``: keeping
annotations as real objects keeps Pydantic's runtime introspection
unambiguous (same rationale as ``cli.py``).
"""

import datetime
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

SCHEMA_VERSION = "1.0"

Difficulty = Literal["easy", "medium", "hard"]
Verdict = Literal["true_positive", "false_positive", "benign"]
Via = Literal["direct", "ssh", "rce_sim"]
Category = Literal[
    "initial_access",
    "execution",
    "persistence",
    "privilege_escalation",
    "defense_evasion",
    "credential_access",
    "discovery",
    "lateral_movement",
    "collection",
    "command_and_control",
    "exfiltration",
    "impact",
    "benign_admin",
    "benign_user",
    "misconfigured_tool",
]

_ID_RE = re.compile(r"^SCN-\d{3}$")


class _Model(BaseModel):
    # Reject unknown keys so a typo'd scenario field fails validation
    # loudly rather than being silently ignored.
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SetupAction(_Model):
    """A one-time, idempotent pre-condition (schema §8)."""

    actor: str
    command: str
    description: str


class Step(_Model):
    """A single action executed by the runner (schema §4)."""

    actor: str
    description: str
    command: str
    via: Via = "direct"
    from_: str | None = Field(default=None, alias="from")
    as_user: str | None = None
    delay_seconds: int = 0
    timeout_seconds: int = 30
    expect_failure: bool = False

    @model_validator(mode="after")
    def _from_required_when_not_direct(self) -> "Step":
        if self.via != "direct" and not self.from_:
            raise ValueError(f"`from` is required when via != direct (via={self.via!r})")
        return self


class ExpectedAlert(_Model):
    """A Wazuh alert the lab should emit — integrity check, not grading (schema §5)."""

    rule_id: int
    description: str | None = None
    minimum_count: int = 1
    timeframe_seconds: int = 300


class Observable(_Model):
    """An IoC (schema §2 expected_observables / §6 answer_key)."""

    type: str
    value: str
    role: str | None = None


class RequiredEnrichment(_Model):
    observable_type: str
    analyzer: str
    required: bool = False


class KeywordGroup(_Model):
    any_of: list[str]


class AnswerKey(_Model):
    """The correct triage outcome the scorer compares against (schema §6)."""

    verdict: Verdict
    severity: Literal["low", "medium", "high", "critical"]
    confidence: Literal["low", "medium", "high"]
    required_observables: list[Observable] = Field(default_factory=list)
    required_enrichment: list[RequiredEnrichment] = Field(default_factory=list)
    summary_keywords: list[KeywordGroup] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    reasoning: str = ""


class Scenario(_Model):
    """A full scenario spec (schema §2 top-level)."""

    schema_version: str
    id: str
    name: str
    description: str
    author: str
    created: datetime.date
    difficulty: Difficulty
    category: Category
    expected_verdict: Verdict
    mitre: list[str] = Field(default_factory=list)
    duration_minutes: int
    requires: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    setup: list[SetupAction] = Field(default_factory=list)
    steps: list[Step]
    expected_alerts: list[ExpectedAlert]
    expected_observables: list[Observable] = Field(default_factory=list)
    hints: list[str] = Field(default_factory=list)
    answer_key: AnswerKey
    scoring_weights: dict[str, float] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def _schema_version_locked(cls, v: str) -> str:
        if v != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION!r}, got {v!r}")
        return v

    @field_validator("id")
    @classmethod
    def _id_format(cls, v: str) -> str:
        if not _ID_RE.match(v):
            raise ValueError(f"id must match SCN-NNN (got {v!r})")
        return v

    @field_validator("mitre")
    @classmethod
    def _mitre_format(cls, v: list[str]) -> list[str]:
        for t in v:
            if not re.match(r"^T\d{4}(\.\d{3})?$", t):
                raise ValueError(f"mitre technique must be Txxxx or Txxxx.yyy (got {t!r})")
        return v

    @model_validator(mode="after")
    def _mitre_required_for_tp(self) -> "Scenario":
        if self.expected_verdict == "true_positive" and not self.mitre:
            raise ValueError("mitre is required when expected_verdict is true_positive")
        return self


class ScenarioError(ValueError):
    """One CLI-friendly error for any scenario load/validate failure.

    The CLI (``wachturm scenario validate``) and the runner catch this
    and print a single clean line — never a raw YAML or Pydantic
    traceback at the user.
    """


def load_scenario(path: Path | str) -> Scenario:
    """Load and validate a scenario YAML file into a :class:`Scenario`.

    Raises :class:`ScenarioError` (only) on a missing file, malformed
    YAML, or a schema violation — with the offending path in the
    message so the operator knows which file failed.
    """
    p = Path(path)
    if not p.is_file():
        raise ScenarioError(f"scenario file not found: {p}")
    try:
        raw = yaml.safe_load(p.read_text())
    except yaml.YAMLError as exc:
        raise ScenarioError(f"invalid YAML in {p}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ScenarioError(f"invalid YAML in {p}: expected a mapping at the top level")
    try:
        return Scenario.model_validate(raw)
    except ValidationError as exc:
        raise ScenarioError(f"{p}: schema validation failed:\n{exc}") from exc
