"""No-spoiler lint for scenario student-facing strings (P3a-0.3).

A Wachturm scenario's ``name``, ``description``, and brief title must
read like a real SOC queue ticket — the alert and the asset — and must
never reveal the disposition (TP / FP / benign). The student discovers
the verdict by investigating; a title that gives it away defeats the
exercise.

``find_spoilers`` is the pure detector. CI runs it over every scenario
(``tests/test_scenario_trio.py``) so a spoiler title cannot merge.

The banned set is deliberately narrow: verdict *tells* only. Alert and
technique vocabulary a real SIEM ticket genuinely contains — brute
force, malware signature, web-attack pattern, persistence, beaconing,
anomalous, port scan — is allowed. Banning it would make an honest
no-spoiler title impossible, which is the opposite of the goal.
"""

import re

# Each pattern matches a phrase that states or strongly implies the
# verdict. Case-insensitive. Word boundaries keep "malware" (an alert
# term) from tripping the "malicious" (a verdict term) rule, etc.
_SPOILER_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"true[\s-]?positive",
        r"false[\s-]?positive",
        r"\bbenign\b",
        r"\bauthoris(?:e|ed|ation)\b",
        r"\bauthoriz(?:e|ed|ation)\b",
        r"\blegitimate\b",
        r"\bmalicious\b",
        r"\bcompromis(?:e|ed|ing)\b",
        r"\bmistyp(?:e|ed|ing)\b",
        r"\btypo\b",
        r"fat[\s-]?finger",
        r"human error",
        r"no incident",
        r"not (?:an )?attack",
        r"not malicious",
        r"\bnuisance\b",
        r"the verdict is",
        r"this is (?:a )?(?:true|false|benign)",
    )
)


def find_spoilers(text: str) -> list[str]:
    """Return the verdict-revealing substrings in ``text``.

    Empty list means the string is no-spoiler-clean. The returned tokens
    are the actual matched text (lower-cased, de-duplicated, sorted) so
    a failing CI message can name exactly what to rewrite.
    """
    hits: set[str] = set()
    for pat in _SPOILER_PATTERNS:
        for m in pat.finditer(text):
            hits.add(m.group(0).lower())
    return sorted(hits)
