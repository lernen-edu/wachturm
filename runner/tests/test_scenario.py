"""Tests for the scenario schema models (canonical impl of SCENARIO_SCHEMA v1.0).

Per SCENARIO_SCHEMA.md §10 the Pydantic models in ``wachturm.scenario``
are the canonical implementation of the locked YAML schema; if the doc
and the models disagree, the models win. These tests pin the model to
the locked schema — starting from the schema's own §9 worked example.
"""

import textwrap

import pytest
import yaml

from wachturm.scenario import Scenario

# Verbatim copy of the SCENARIO_SCHEMA.md §9 "Full example" — the locked
# schema's own canonical scenario. It MUST parse.
CANONICAL_SCHEMA_EXAMPLE = textwrap.dedent("""
    schema_version: "1.0"
    id: SCN-001
    name: "SSH Brute Force into Successful Login"
    description: >
      An attacker brute-forces SSH credentials against the jump host and
      eventually succeeds, then performs basic post-auth reconnaissance.
    author: "Wachturm Contributors"
    created: 2026-05-15
    difficulty: easy
    category: initial_access
    expected_verdict: true_positive
    mitre:
      - T1110.001
      - T1078
    duration_minutes: 4
    tags: [ssh, credential-access, beginner]

    setup:
      - actor: vic-jump
        command: "useradd -m -s /bin/bash admin || true; echo 'admin:Sup3rs3cret!' | chpasswd"
        description: "Ensure target user exists"

    steps:
      - actor: atk-kali
        description: "Quick port scan"
        command: "nmap -Pn -p 22 10.50.10.30"
        delay_seconds: 0

      - actor: atk-kali
        description: "Brute force SSH (will find creds in the seeded wordlist)"
        command: "hydra -l admin -P /opt/wordlists/wachturm-easy.txt -t 4 -f ssh://10.50.10.30"
        delay_seconds: 10
        timeout_seconds: 120

      - actor: atk-kali
        description: "Post-auth recon over SSH"
        command: "sshpass -p 'Sup3rs3cret!' ssh admin@10.50.10.30 whoami"
        delay_seconds: 5
        timeout_seconds: 30

    expected_alerts:
      - rule_id: 5710
        minimum_count: 5
        timeframe_seconds: 180
      - rule_id: 5712
        minimum_count: 1
        timeframe_seconds: 180
      - rule_id: 5715
        minimum_count: 1
        timeframe_seconds: 240

    expected_observables:
      - type: ip
        value: "10.50.20.10"
      - type: hostname
        value: "vic-jump"
      - type: user
        value: "admin"

    hints:
      - "Check the timing and source of the failed login attempts on vic-jump."
      - "Did the eventual successful login come from the same source as the failures?"
      - "Pivot to the post-auth commands — what did the attacker do once in?"

    answer_key:
      verdict: true_positive
      severity: high
      confidence: high
      required_observables:
        - type: ip
          value: "10.50.20.10"
          role: source
        - type: hostname
          value: "vic-jump"
          role: target
        - type: user
          value: "admin"
          role: compromised
      summary_keywords:
        - any_of: ["brute force", "brute-force", "password guessing"]
        - any_of: ["successful login", "compromise", "authenticated"]
      next_steps:
        - contain_host
        - reset_credentials
        - escalate_t2
      reasoning: >
        A sustained burst of failed SSH login attempts from a single source IP
        followed by a successful authentication is a textbook compromise.
    """)


def test_canonical_schema_example_parses() -> None:
    """The schema's own §9 example must validate into the model."""
    scn = Scenario.model_validate(yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE))

    assert scn.schema_version == "1.0"
    assert scn.id == "SCN-001"
    assert scn.expected_verdict == "true_positive"
    assert scn.difficulty == "easy"
    assert scn.category == "initial_access"
    assert scn.mitre == ["T1110.001", "T1078"]
    assert len(scn.steps) == 3
    assert scn.steps[0].delay_seconds == 0
    assert scn.steps[1].timeout_seconds == 120
    assert scn.steps[2].timeout_seconds == 30
    assert scn.expected_alerts[0].rule_id == 5710
    assert scn.expected_alerts[0].minimum_count == 5
    assert scn.answer_key.verdict == "true_positive"
    assert scn.answer_key.severity == "high"
    assert len(scn.hints) == 3


def test_step_defaults_apply() -> None:
    """Unspecified step fields take the schema §4 defaults."""
    scn = Scenario.model_validate(yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE))
    # step 0 specified no timeout_seconds -> default 30; no via -> "direct"
    assert scn.steps[0].timeout_seconds == 30
    assert scn.steps[0].via == "direct"
    assert scn.steps[0].expect_failure is False


def test_mitre_required_when_true_positive() -> None:
    """SCENARIO_SCHEMA §2: mitre is required iff expected_verdict is TP."""
    data = yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE)
    del data["mitre"]
    with pytest.raises(ValueError, match="mitre"):
        Scenario.model_validate(data)


def test_mitre_optional_for_false_positive() -> None:
    """A non-TP scenario may omit mitre entirely."""
    data = yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE)
    del data["mitre"]
    data["expected_verdict"] = "false_positive"
    data["answer_key"]["verdict"] = "false_positive"
    scn = Scenario.model_validate(data)
    assert scn.mitre == []


def test_bad_id_format_rejected() -> None:
    """`id` must match SCN-NNN (schema §2)."""
    data = yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE)
    data["id"] = "SCN1"
    with pytest.raises(ValueError, match="id"):
        Scenario.model_validate(data)


def test_unknown_category_rejected() -> None:
    """`category` is a closed enum (schema §3)."""
    data = yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE)
    data["category"] = "not_a_category"
    with pytest.raises(ValueError):
        Scenario.model_validate(data)


def test_step_via_ssh_requires_from() -> None:
    """schema §4: `from` is required when `via != direct`."""
    data = yaml.safe_load(CANONICAL_SCHEMA_EXAMPLE)
    data["steps"][0]["via"] = "ssh"  # no `from`
    with pytest.raises(ValueError, match="from"):
        Scenario.model_validate(data)
