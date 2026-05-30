"""Wazuh alert timestamp parsing must be timezone-correct.

The e2e gate exposed a real bug: alert timestamps were parsed with
``time.mktime`` (LOCAL tz) but compared against ``time.time()`` (UTC
epoch), shifting every alert out of the integrity window so a working
lab (10 alerts) reported 0. The parser must yield an absolute UTC epoch
regardless of the offset in the string.
"""

from datetime import UTC, datetime

from wachturm.runner import parse_wazuh_timestamp


def test_utc_offset_parses_to_absolute_epoch() -> None:
    got = parse_wazuh_timestamp("2026-05-16T23:31:51.123+0000")
    expected = datetime(2026, 5, 16, 23, 31, 51, 123000, tzinfo=UTC).timestamp()
    assert abs(got - expected) < 0.001


def test_same_instant_different_offset_is_equal() -> None:
    a = parse_wazuh_timestamp("2026-05-16T23:31:51.000+0000")
    b = parse_wazuh_timestamp("2026-05-16T18:31:51.000-0500")  # same instant
    assert abs(a - b) < 0.001


def test_no_fractional_seconds_still_parses() -> None:
    got = parse_wazuh_timestamp("2026-05-16T23:31:51+0000")
    expected = datetime(2026, 5, 16, 23, 31, 51, tzinfo=UTC).timestamp()
    assert abs(got - expected) < 0.001


def test_unparseable_returns_zero() -> None:
    assert parse_wazuh_timestamp("not-a-timestamp") == 0.0
    assert parse_wazuh_timestamp("") == 0.0
