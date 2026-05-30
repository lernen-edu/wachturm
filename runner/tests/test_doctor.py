"""Unit test for the one pure helper in doctor (env-independent)."""

from wachturm.doctor import _to_gib


def test_to_gib_converts_bytes() -> None:
    assert _to_gib(1024**3) == 1.0
    assert _to_gib(16 * 1024**3) == 16.0
    assert _to_gib(0) == 0.0
