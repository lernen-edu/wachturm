"""TDD for wachturm.scenario_lint (P3a-0.3).

A scenario's student-facing strings (``name``, ``description``, brief
title) must read like a real SOC queue ticket — the alert and the asset
— and must NEVER reveal whether the answer is TP / FP / benign. The
student discovers the verdict by investigating. ``find_spoilers`` is
the pure detector CI enforces.

The banned set is verdict-*tells* only. Alert/technique vocabulary that
a real SIEM ticket genuinely contains — "brute-force", "malware
signature", "web attack pattern", "persistence", "beaconing",
"anomalous" — is explicitly allowed; banning it would make honest
no-spoiler titles impossible.
"""

from wachturm.scenario_lint import find_spoilers


def test_flags_the_old_pre_despoiler_names() -> None:
    # The exact strings 0.2 removed — the regression this guards.
    assert find_spoilers("Authorized Vulnerability Scan Triggers Brute-Force Alerts")
    assert find_spoilers("User Mistyped Password, Then Logged In")
    assert find_spoilers("A textbook false positive: authorized, documented tooling")
    assert find_spoilers("Benign: human error, no incident")
    assert find_spoilers("A textbook credential compromise: the verdict is true positive")


def test_passes_the_locked_no_spoiler_names() -> None:
    clean = [
        "SSH brute-force alert — vic-jump",
        "Recurring SSH brute-force alert — vic-jump",
        "SSH authentication failures then success — bobsmith / vic-jump",
        "Known-malware signature detected on vic-work",
        "Unusual off-hours mass file-access on vic-work",
        "Outbound connection to a threat-flagged IP — vic-work",
        "Internal port scan across the victim subnet",
        "Web-application attack pattern against /login — vic-web",
        "Anomalous login followed by account changes — vic-dc",
        "Geo-anomalous login for a domain user — vic-dc",
        "New scheduled-task/cron persistence on vic-web",
        "Periodic outbound beaconing pattern — vic-work",
        "Off-hours administrative remote access — vic-jump",
        "Repeated MFA prompts and a new mailbox rule — vic-dc",
        "Anomalous DNS query volume — vic-work",
    ]
    for name in clean:
        assert find_spoilers(name) == [], f"false-positive spoiler flag on: {name!r}"


def test_is_case_insensitive_and_returns_the_offending_tokens() -> None:
    hits = find_spoilers("This is BENIGN and clearly Not Malicious")
    assert any("benign" in h.lower() for h in hits)
    assert any("malicious" in h.lower() for h in hits)
