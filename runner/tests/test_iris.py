"""TDD for wachturm.integrations.iris (P2-M1 IRIS token bootstrap).

The two unavoidable IO boundaries are injected so this runs with no lab:
  * the ``docker exec iris-db psql`` call -> an ``Executor`` callable
    (same shape as ``wachturm.cli._docker_exec``);
  * the IRIS HTTPS API -> an ``httpx.MockTransport``.
Real production code paths are exercised; only the boundaries are fakes.
"""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from wachturm.integrations.iris import (
    IrisError,
    bootstrap,
    read_admin_api_key,
    verify_api_key,
    write_token_file,
)

Executor = Callable[[list[str], int], tuple[int, str, str]]
_KEY = "siv7" + "a" * 82  # 86 chars, like the real IRIS admin api_key


def _exec_returning(rc: int, out: str, err: str = "") -> tuple[Executor, list[list[str]]]:
    """An Executor that always returns (rc, out, err); records argvs."""
    seen: list[list[str]] = []

    def _e(argv: list[str], timeout: int) -> tuple[int, str, str]:
        seen.append(argv)
        return (rc, out, err)

    return _e, seen


def _ping_transport(
    status: int, body: dict[str, object], *, captured: list[httpx.Request] | None = None
) -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        if captured is not None:
            captured.append(request)
        return httpx.Response(status, json=body)

    return httpx.MockTransport(_handler)


# ── read_admin_api_key ───────────────────────────────────────────────


def test_read_admin_api_key_returns_stripped_key() -> None:
    execute, _ = _exec_returning(0, _KEY + "\n")
    assert read_admin_api_key(execute) == _KEY


def test_read_admin_api_key_builds_expected_argv() -> None:
    execute, seen = _exec_returning(0, _KEY)
    read_admin_api_key(execute, container="iris-db", db_user="iris", db_name="iris_db")
    assert seen == [
        [
            "docker",
            "exec",
            "iris-db",
            "psql",
            "-U",
            "iris",
            "-d",
            "iris_db",
            "-tAc",
            'SELECT api_key FROM "user" WHERE id = 1',
        ]
    ]


def test_read_admin_api_key_raises_on_nonzero_exit() -> None:
    execute, _ = _exec_returning(1, "", "could not connect")
    with pytest.raises(IrisError, match="psql"):
        read_admin_api_key(execute)


def test_read_admin_api_key_raises_on_empty() -> None:
    execute, _ = _exec_returning(0, "   \n")
    with pytest.raises(IrisError, match="empty"):
        read_admin_api_key(execute)


def test_read_admin_api_key_raises_on_implausibly_short() -> None:
    execute, _ = _exec_returning(0, "short")
    with pytest.raises(IrisError, match="implausible|short|length"):
        read_admin_api_key(execute)


# ── write_token_file ─────────────────────────────────────────────────


def test_write_token_file_is_0600_with_content(tmp_path: Path) -> None:
    dest = tmp_path / "sub" / "iris.token"
    out = write_token_file(_KEY, path=dest)
    assert out == dest
    assert dest.read_text() == _KEY
    assert (dest.stat().st_mode & 0o777) == 0o600


def test_write_token_file_creates_private_parent(tmp_path: Path) -> None:
    dest = tmp_path / "newdir" / "iris.token"
    write_token_file(_KEY, path=dest)
    assert (dest.parent.stat().st_mode & 0o777) == 0o700


# ── verify_api_key ───────────────────────────────────────────────────


def test_verify_api_key_ok_sends_bearer_to_ping() -> None:
    seen: list[httpx.Request] = []
    t = _ping_transport(200, {"status": "success", "message": "pong", "data": []}, captured=seen)
    verify_api_key("https://127.0.0.1:9000", _KEY, transport=t)
    assert len(seen) == 1
    assert seen[0].url.path == "/api/ping"
    assert seen[0].headers["authorization"] == f"Bearer {_KEY}"


def test_verify_api_key_raises_on_401() -> None:
    t = _ping_transport(401, {"status": "error", "message": "Unauthorized"})
    with pytest.raises(IrisError):
        verify_api_key("https://127.0.0.1:9000", _KEY, transport=t)


def test_verify_api_key_raises_on_unexpected_body() -> None:
    t = _ping_transport(200, {"unexpected": True})
    with pytest.raises(IrisError):
        verify_api_key("https://127.0.0.1:9000", _KEY, transport=t)


# ── bootstrap (compose) ──────────────────────────────────────────────


def test_bootstrap_writes_token_and_verifies(tmp_path: Path) -> None:
    execute, _ = _exec_returning(0, _KEY)
    dest = tmp_path / "iris.token"
    t = _ping_transport(200, {"status": "success", "message": "pong", "data": []})
    out = bootstrap(execute, base_url="https://127.0.0.1:9000", token_path=dest, transport=t)
    assert out == dest
    assert dest.read_text() == _KEY
    assert (dest.stat().st_mode & 0o777) == 0o600


def test_bootstrap_retries_verify_then_succeeds(tmp_path: Path) -> None:
    execute, _ = _exec_returning(0, _KEY)
    dest = tmp_path / "iris.token"
    calls = {"n": 0}

    def _handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503, json={"status": "error"})
        return httpx.Response(200, json={"status": "success", "message": "pong"})

    slept: list[float] = []
    out = bootstrap(
        execute,
        base_url="https://127.0.0.1:9000",
        token_path=dest,
        transport=httpx.MockTransport(_handler),
        retries=5,
        sleep=slept.append,
    )
    assert out == dest
    assert calls["n"] == 3
    assert len(slept) == 2  # two failed attempts -> two backoff sleeps


def test_bootstrap_raises_when_key_read_fails(tmp_path: Path) -> None:
    execute, _ = _exec_returning(1, "", "psql: connection refused")
    dest = tmp_path / "iris.token"
    with pytest.raises(IrisError):
        bootstrap(execute, base_url="https://127.0.0.1:9000", token_path=dest)
    assert not dest.exists()  # no half-written token on failure
