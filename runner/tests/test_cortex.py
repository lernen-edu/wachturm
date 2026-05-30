"""TDD for wachturm.integrations.cortex (P2-M4 Cortex bootstrap).

Unlike the IRIS bootstrap (which had to read a key out of iris-db over
``docker exec``), the *entire* Cortex 3.1.8 headless bootstrap is HTTP —
so the single injected IO boundary is an ``httpx.MockTransport``. Real
production code paths are exercised; only the Cortex API is faked.

The contract these tests pin was derived empirically against the running
thehiveproject/cortex:3.1.8 image (M4 grounding):
  * ``POST /api/maintenance/migrate`` -> 204
  * poll ``GET /api/user/current`` until 404 "user init not found"
  * ``POST /api/user`` (unauth init window) creates the superadmin
  * ``POST /api/login`` -> CORTEX_SESSION cookie; a follow-up safe GET
    mints the CORTEX-XSRF-TOKEN cookie; session POSTs must echo it in
    the X-CORTEX-XSRF-TOKEN header
  * a Bearer api-key bypasses CSRF for everything else
"""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from wachturm.integrations.cortex import (
    CortexError,
    bootstrap,
    create_org,
    create_superadmin,
    enable_analyzer,
    migrate,
    session_login,
    set_user_password,
    verify_api_key,
    wait_user_init,
    write_token_file,
)

_KEY = "N+Ys6OfPS4o5N3Mdcc+RNS5ZffW60cNL"  # 32 chars, base64-ish like a real one
_BASE = "http://127.0.0.1:9001"


_Handler = Callable[[httpx.Request], httpx.Response]


class _Router:
    """A scriptable MockTransport: (METHOD, path) -> (status, json|text).

    A route value may instead be a ``_Handler`` callable for stateful
    cases (cookies, conflict-then-ok). Records every request.
    """

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], tuple[int, object] | _Handler] = {}
        self.seen: list[httpx.Request] = []

    def on(self, method: str, path: str, status: int, body: object = None) -> "_Router":
        self.routes[(method, path)] = (status, body)
        return self

    def on_call(self, method: str, path: str, fn: _Handler) -> "_Router":
        self.routes[(method, path)] = fn
        return self

    def transport(self) -> httpx.MockTransport:
        def _h(request: httpx.Request) -> httpx.Response:
            self.seen.append(request)
            entry = self.routes.get((request.method, request.url.path))
            if entry is None:
                return httpx.Response(599, json={"type": "Unrouted", "message": request.url.path})
            if isinstance(entry, tuple):
                status, body = entry
                if isinstance(body, (dict, list)):
                    return httpx.Response(status, json=body)
                return httpx.Response(status, text=("" if body is None else str(body)))
            return entry(request)

        return httpx.MockTransport(_h)


# ── write_token_file (mirrors M1 iris.write_token_file exactly) ──────


def test_write_token_file_is_0600_with_content(tmp_path: Path) -> None:
    dest = tmp_path / "sub" / "cortex.token"
    out = write_token_file(_KEY, path=dest)
    assert out == dest
    assert dest.read_text() == _KEY
    assert (dest.stat().st_mode & 0o777) == 0o600


def test_write_token_file_creates_private_parent(tmp_path: Path) -> None:
    dest = tmp_path / "nd" / "cortex.token"
    write_token_file(_KEY, path=dest)
    assert (dest.parent.stat().st_mode & 0o777) == 0o700


# ── verify_api_key ──────────────────────────────────────────────────


def test_verify_api_key_ok_sends_bearer() -> None:
    r = _Router().on("GET", "/api/user/current", 200, {"id": "wachturm-svc"})
    verify_api_key(_BASE, _KEY, transport=r.transport())
    assert r.seen[0].headers["authorization"] == f"Bearer {_KEY}"


def test_verify_api_key_raises_on_401() -> None:
    r = _Router().on("GET", "/api/user/current", 401, {"type": "AuthenticationError"})
    with pytest.raises(CortexError):
        verify_api_key(_BASE, _KEY, transport=r.transport())


# ── migrate ─────────────────────────────────────────────────────────


def test_migrate_accepts_204() -> None:
    r = _Router().on("POST", "/api/maintenance/migrate", 204)
    migrate(_BASE, transport=r.transport())  # no raise
    assert r.seen[0].method == "POST"


def test_migrate_raises_on_500() -> None:
    r = _Router().on("POST", "/api/maintenance/migrate", 500, {"type": "Err"})
    with pytest.raises(CortexError):
        migrate(_BASE, transport=r.transport())


# ── wait_user_init ──────────────────────────────────────────────────


def test_wait_user_init_polls_until_sentinel() -> None:
    seq = [
        httpx.Response(520, json={"type": "MigrationError"}),
        httpx.Response(520, json={"type": "MigrationError"}),
        httpx.Response(404, json={"type": "NotFoundError", "message": "user init not found"}),
    ]
    box = {"i": 0}

    def _fn(_request: httpx.Request) -> httpx.Response:
        resp = seq[box["i"]]
        box["i"] += 1
        return resp

    r = _Router().on_call("GET", "/api/user/current", _fn)
    slept: list[float] = []
    wait_user_init(_BASE, transport=r.transport(), retries=5, sleep=slept.append)
    assert box["i"] == 3
    assert len(slept) == 2


def test_wait_user_init_raises_if_never() -> None:
    r = _Router().on("GET", "/api/user/current", 520, {"type": "MigrationError"})
    with pytest.raises(CortexError):
        wait_user_init(_BASE, transport=r.transport(), retries=3, sleep=lambda _s: None)


# ── create_superadmin ───────────────────────────────────────────────


def test_create_superadmin_posts_password_in_body() -> None:
    r = _Router().on("POST", "/api/user", 201, {"id": "admin", "createdBy": "init"})
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    create_superadmin(client, login="admin", name="Wachturm Admin", password="pw")
    import json as _j

    body = _j.loads(r.seen[0].content)
    assert body["login"] == "admin"
    assert body["password"] == "pw"
    assert body["roles"] == ["superadmin"]
    assert body["organization"] == "cortex"


def test_create_superadmin_conflict_is_idempotent() -> None:
    r = _Router().on("POST", "/api/user", 409, {"type": "ConflictError"})
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    create_superadmin(client, login="admin", name="A", password="pw")  # no raise


# ── session_login (cookie + CSRF mint) ──────────────────────────────


def test_session_login_returns_csrf_from_cookie() -> None:
    def _login(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"id": "admin"},
            headers={"set-cookie": "CORTEX_SESSION=sess-abc; Path=/; HttpOnly"},
        )

    def _current(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"id": "admin"},
            headers={"set-cookie": "CORTEX-XSRF-TOKEN=csrf-xyz; Path=/"},
        )

    r = _Router()
    r.on_call("POST", "/api/login", _login)
    r.on_call("GET", "/api/user/current", _current)
    client, csrf = session_login(_BASE, user="admin", password="pw", transport=r.transport())
    assert csrf == "csrf-xyz"
    client.close()


# ── create_org / enable_analyzer (Bearer; conflict idempotent) ───────


def test_create_org_posts_active_status() -> None:
    r = _Router().on("POST", "/api/organization", 201, {"id": "wachturm"})
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    create_org(client, name="wachturm", description="lab")
    import json as _j

    body = _j.loads(r.seen[0].content)
    assert body["name"] == "wachturm"
    assert body["status"] == "Active"


def test_enable_analyzer_conflict_is_idempotent() -> None:
    r = _Router().on(
        "POST", "/api/organization/analyzer/MaxMind_GeoIP_4_0", 409, {"type": "ConflictError"}
    )
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    enable_analyzer(client, "MaxMind_GeoIP_4_0")  # no raise


def test_enable_analyzer_sends_expected_body() -> None:
    r = _Router().on("POST", "/api/organization/analyzer/AbuseIPDB_2_0", 201, {"_id": "x"})
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    enable_analyzer(client, "AbuseIPDB_2_0", configuration={"key": "secret", "days": 30})
    import json as _j

    body = _j.loads(r.seen[0].content)
    assert body["name"] == "AbuseIPDB_2_0"
    assert body["configuration"]["key"] == "secret"
    assert body["jobCache"] == 10


# ── bootstrap orchestration ─────────────────────────────────────────


def _full_bootstrap_router() -> _Router:
    """Routes a clean fresh-lab bootstrap end to end."""
    r = _Router()
    r.on("POST", "/api/maintenance/migrate", 204)
    state = {"users": 0}

    def _current(request: httpx.Request) -> httpx.Response:
        # Bearer => authed 200; cookie session GET => mint CSRF; else sentinel
        if request.headers.get("authorization", "").startswith("Bearer "):
            return httpx.Response(200, json={"id": "x"})
        if "CORTEX_SESSION" in request.headers.get("cookie", ""):
            return httpx.Response(
                200, json={"id": "admin"}, headers={"set-cookie": "CORTEX-XSRF-TOKEN=ct; Path=/"}
            )
        if state["users"] == 0:
            return httpx.Response(
                404, json={"type": "NotFoundError", "message": "user init not found"}
            )
        return httpx.Response(401, json={"type": "AuthenticationError"})

    def _create_user(_request: httpx.Request) -> httpx.Response:
        state["users"] += 1
        return httpx.Response(201, json={"id": "u", "createdBy": "init"})

    r.on_call("GET", "/api/user/current", _current)
    r.on_call("POST", "/api/user", _create_user)
    r.on_call(
        "POST",
        "/api/login",
        lambda _q: httpx.Response(
            200, json={"id": "admin"}, headers={"set-cookie": "CORTEX_SESSION=s; Path=/"}
        ),
    )
    r.on("POST", "/api/user/admin/key/renew", 200, "ADMINKEY1234567890")
    r.on("POST", "/api/user/wachturm-svc/key/renew", 200, _KEY)
    r.on("POST", "/api/organization", 201, {"id": "wachturm"})
    r.on("PATCH", "/api/user/wachturm-svc", 200, {"id": "wachturm-svc"})
    r.on("POST", "/api/user/wachturm-svc/password/set", 204)
    for a in ("ValidateObservable_1_0", "DShield_lookup_1_0", "AbuseIPDB_2_0"):
        r.on("POST", f"/api/organization/analyzer/{a}", 201, {"_id": a})
    return r


def test_bootstrap_fresh_writes_svc_token(tmp_path: Path) -> None:
    dest = tmp_path / "cortex.token"
    r = _full_bootstrap_router()
    out = bootstrap(base_url=_BASE, token_path=dest, transport=r.transport(), sleep=lambda _s: None)
    assert out == dest
    assert dest.read_text() == _KEY
    assert (dest.stat().st_mode & 0o777) == 0o600
    enabled = [s.url.path for s in r.seen if s.url.path.startswith("/api/organization/analyzer/")]
    assert "/api/organization/analyzer/ValidateObservable_1_0" in enabled
    assert "/api/organization/analyzer/DShield_lookup_1_0" in enabled


def test_set_user_password_posts_to_password_set() -> None:
    r = _Router().on("POST", "/api/user/wachturm-svc/password/set", 204)
    client = httpx.Client(base_url=_BASE, transport=r.transport())
    set_user_password(client, "wachturm-svc", "wachturm-analyst")
    import json as _j

    assert _j.loads(r.seen[0].content)["password"] == "wachturm-analyst"


def test_bootstrap_sets_svc_ui_password(tmp_path: Path) -> None:
    r = _full_bootstrap_router()
    bootstrap(
        base_url=_BASE, token_path=tmp_path / "t", transport=r.transport(), sleep=lambda _s: None
    )
    assert "/api/user/wachturm-svc/password/set" in [s.url.path for s in r.seen]


def test_bootstrap_skips_when_token_valid(tmp_path: Path) -> None:
    dest = tmp_path / "cortex.token"
    dest.write_text(_KEY)
    # Only /api/user/current (Bearer) is routed: a full bootstrap would 599.
    r = _Router().on("GET", "/api/user/current", 200, {"id": "wachturm-svc"})
    out = bootstrap(base_url=_BASE, token_path=dest, transport=r.transport())
    assert out == dest
    assert [s.url.path for s in r.seen] == ["/api/user/current"]


def test_bootstrap_enables_abuseipdb_only_with_key(tmp_path: Path) -> None:
    r = _full_bootstrap_router()
    bootstrap(
        base_url=_BASE,
        token_path=tmp_path / "t",
        transport=r.transport(),
        sleep=lambda _s: None,
        abuseipdb_key=None,
    )
    paths = [s.url.path for s in r.seen]
    assert "/api/organization/analyzer/AbuseIPDB_2_0" not in paths
    assert "/api/organization/analyzer/ValidateObservable_1_0" in paths
