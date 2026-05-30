"""Phase 0 smoke test: the package imports and exposes a version string.

Exists so `pytest` collects at least one test (CI must not red on an
empty suite). Real runner/scoring tests arrive in Phase 1+.
"""

import wachturm
from wachturm.cli import app


def test_package_exposes_version_string() -> None:
    assert isinstance(wachturm.__version__, str)
    assert wachturm.__version__


def test_cli_app_constructed() -> None:
    assert app is not None
