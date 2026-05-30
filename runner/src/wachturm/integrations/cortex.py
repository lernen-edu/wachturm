"""Cortex 3.1.8 headless bootstrap (P2-M4).

DFIR-IRIS ships **no** Cortex module (verified: not in the image, not in
the official dfir-iris org, not on PyPI — Cortex is TheHive's companion,
never IRIS's). So Phase 2 uses the *documented-pivot* model: the IRIS
case already carries the observable as an IOC (M3); the analyst pivots
to a fully-provisioned Cortex on loopback, runs an analyzer on that
observable, and records the verdict back in the IRIS case. This module
provisions the Cortex side so that pivot works out of the box.

Unlike the IRIS bootstrap (M1), there is no datastore to read — the
*entire* Cortex bootstrap is its HTTP API, so the single injected IO
boundary is an ``httpx`` transport (unit-tested with ``MockTransport``,
no running lab). The contract below was derived empirically against the
running ``thehiveproject/cortex:3.1.8`` image:

  * ``POST /api/maintenance/migrate`` -> 204 (async; pre-migrate the API
    answers 520, post-migrate 404 "user init not found").
  * The unauth *init window* (open only while zero users exist) allows
    exactly one ``POST /api/user`` to create the first superadmin.
  * ``auth.method.basic = false`` -> auth is a session cookie
    (``POST /api/login`` -> ``CORTEX_SESSION``) **or** a Bearer api-key.
  * Session POSTs need the CSRF token (cookie ``CORTEX-XSRF-TOKEN``,
    minted on a safe GET, echoed in header ``X-CORTEX-XSRF-TOKEN``); a
    Bearer api-key bypasses CSRF, so it is used for everything after the
    first key is minted.
  * Enabling analyzers needs the **orgadmin** role *inside* the org
    (superadmin lives in org ``cortex`` and can only manage orgs/users).

``bootstrap`` is idempotent: a present+valid ``~/.wachturm/cortex.token``
short-circuits the whole thing, and every create is conflict-tolerant,
so ``make up-casemgmt`` can re-run it on every bring-up.
"""

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx


class CortexError(Exception):
    """A recoverable failure in the Cortex bootstrap (mirrors IrisError)."""


_DEFAULT_BASE_URL = "http://127.0.0.1:9001"  # cortex, loopback only, plain http
_DEFAULT_TOKEN_PATH = Path.home() / ".wachturm" / "cortex.token"
_MIN_KEY_LEN = 16  # real Cortex keys are ~32 base64-ish chars; length-only guard
_USER_INIT_SENTINEL = "user init not found"
_CSRF_COOKIE = "CORTEX-XSRF-TOKEN"
_CSRF_HEADER = "X-CORTEX-XSRF-TOKEN"

SUPERADMIN_LOGIN = "admin"
SUPERADMIN_ORG = "cortex"  # the fixed superadmin org in Cortex 3.x
ORG_NAME = "wachturm"
SVC_LOGIN = "wachturm-svc"
SVC_ROLES = ["read", "analyze", "orgadmin"]  # run AND configure analyzers
# Sealed-lab default so a student can log in to the Cortex UI and click
# an analyzer (the documented-pivot model). Same posture as the IRIS
# demo creds; documented by `make first-run-creds`.
SVC_PASSWORD = "wachturm-analyst"

# Keyless analyzers, enabled unconditionally. Selected by *running them*
# in M4 against the lab's real observable — the RFC1918 scenario
# attacker IP (10.50.10.250) — not by trusting the catalog's "no
# required config" flag: MaxMind_GeoIP / Abuse_Finder error on a
# private IP (no geo / no abuse contact), and MISPWarningLists fails
# "wrong configuration settings" without a warninglists dataset. These
# two return Success on BOTH the private scenario IP and public IPs:
#   * ValidateObservable — offline, deterministic, always succeeds:
#     classifies/validates any IOC. The guaranteed DoD floor (the
#     analyst always sees a result, CI-stable, no egress).
#   * DShield_lookup — real keyless SANS-ISC threat intel (is this IP a
#     known scanner/attacker?); "not listed" on an internal IP is
#     itself a valid Tier-1 finding.
# The real ``MISP_2_1`` (needs a server+key) is intentionally left
# unenabled = the Phase-4 slot. AbuseIPDB is opt-in (key required).
KEYLESS_ANALYZERS = ("ValidateObservable_1_0", "DShield_lookup_1_0")
ABUSEIPDB_ANALYZER = "AbuseIPDB_2_0"


def _is_conflict(resp: httpx.Response) -> bool:
    """True if Cortex says the resource already exists (idempotent ok)."""
    if resp.status_code == 409:
        return True
    try:
        return bool(resp.json().get("type") == "ConflictError")
    except ValueError:
        return False


def _api(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    ok: tuple[int, ...] = (200, 201, 204),
    idempotent: bool = False,
) -> httpx.Response:
    """One Cortex API call. Raises CortexError unless status in ``ok``.

    ``idempotent`` swallows an "already exists" conflict so re-running
    the bootstrap is safe.
    """
    try:
        resp = client.request(method, path, json=json_body, headers=headers)
    except httpx.HTTPError as exc:
        raise CortexError(f"Cortex {method} {path} unreachable: {exc}") from exc
    if resp.status_code in ok:
        return resp
    if idempotent and _is_conflict(resp):
        return resp
    raise CortexError(f"Cortex {method} {path} -> HTTP {resp.status_code}: {resp.text[:200]}")


def write_token_file(api_key: str, *, path: Path | None = None) -> Path:
    """Write ``api_key`` 0600 (parent 0700). Mirrors M1 iris.write_token_file.

    Default ~/.wachturm/cortex.token — the credential the documented
    Cortex pivot (and any future automation) reads.
    """
    dest = path if path is not None else _DEFAULT_TOKEN_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(dest.parent, 0o700)
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(api_key)
    os.chmod(dest, 0o600)  # defensive: O_CREAT mode is umask-masked
    return dest


def open_cortex_client(
    base_url: str,
    *,
    api_key: str | None = None,
    timeout: float = 15.0,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client:
    """An httpx client for Cortex; Bearer header set iff ``api_key``.

    Cortex is plain http on loopback (no TLS, unlike iris-nginx). The
    client keeps a cookie jar so the session+CSRF flow works.
    """
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["Authorization"] = f"Bearer {api_key}"
    if transport is not None:
        return httpx.Client(
            base_url=base_url, timeout=timeout, headers=headers, transport=transport
        )
    return httpx.Client(base_url=base_url, timeout=timeout, headers=headers)


def verify_api_key(
    base_url: str,
    api_key: str,
    *,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> None:
    """Confirm ``api_key`` authenticates (GET /api/user/current -> 200)."""
    client = open_cortex_client(base_url, api_key=api_key, timeout=timeout, transport=transport)
    try:
        resp = client.get("/api/user/current")
    except httpx.HTTPError as exc:
        raise CortexError(f"Cortex /api/user/current unreachable: {exc}") from exc
    finally:
        client.close()
    if resp.status_code != 200:
        raise CortexError(f"Cortex api-key rejected (HTTP {resp.status_code})")


def migrate(
    base_url: str,
    *,
    timeout: float = 60.0,
    transport: httpx.BaseTransport | None = None,
) -> None:
    """POST /api/maintenance/migrate (unauth, idempotent). Expects 204/200."""
    client = open_cortex_client(base_url, timeout=timeout, transport=transport)
    try:
        _api(client, "POST", "/api/maintenance/migrate", ok=(200, 204))
    finally:
        client.close()


def wait_user_init(
    base_url: str,
    *,
    transport: httpx.BaseTransport | None = None,
    retries: int = 30,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """Poll GET /api/user/current until the "user init not found" sentinel.

    Migration is async: pre-migrate the endpoint answers 520, and only
    once it settles (migrated, zero users) does it answer 404 with that
    message — the signal that the unauth init window is open.
    """
    client = open_cortex_client(base_url, transport=transport)
    try:
        for attempt in range(retries):
            resp = client.get("/api/user/current")
            if resp.status_code == 404 and _USER_INIT_SENTINEL in resp.text:
                return
            if attempt == retries - 1:
                break
            sleep(min(2.0 * (attempt + 1), 10.0))
    finally:
        client.close()
    raise CortexError(
        f"Cortex never reached '{_USER_INIT_SENTINEL}' after {retries} polls (migration stuck?)"
    )


def create_superadmin(client: httpx.Client, *, login: str, name: str, password: str) -> None:
    """Create the first superadmin via the unauth init window.

    Conflict-tolerant: a re-run on an already-initialised Cortex is a
    no-op (the window is closed and the user exists).
    """
    _api(
        client,
        "POST",
        "/api/user",
        json_body={
            "login": login,
            "name": name,
            "password": password,
            "roles": ["superadmin"],
            "organization": SUPERADMIN_ORG,
        },
        ok=(200, 201),
        idempotent=True,
    )


def session_login(
    base_url: str,
    *,
    user: str,
    password: str,
    timeout: float = 15.0,
    transport: httpx.BaseTransport | None = None,
) -> tuple[httpx.Client, str]:
    """Log in with the local password; return (session client, CSRF token).

    ``POST /api/login`` sets the ``CORTEX_SESSION`` cookie; a follow-up
    safe GET makes Cortex mint the ``CORTEX-XSRF-TOKEN`` cookie, which
    session-authenticated POSTs must echo back as a header. The returned
    client carries the session cookie.
    """
    client = open_cortex_client(base_url, timeout=timeout, transport=transport)
    _api(client, "POST", "/api/login", json_body={"user": user, "password": password}, ok=(200,))
    client.get("/api/user/current")  # mints the CSRF cookie
    csrf = client.cookies.get(_CSRF_COOKIE)
    if not csrf:
        client.close()
        raise CortexError("Cortex did not issue a CSRF cookie after login")
    return client, csrf


def _renew_key(client: httpx.Client, login: str, *, csrf: str | None = None) -> str:
    """POST /api/user/<login>/key/renew -> the new api-key (bare text body).

    ``csrf`` is required for session auth; a Bearer client passes None.
    Note: renew *rotates* — only call it when (re)establishing a token.
    """
    headers = {_CSRF_HEADER: csrf} if csrf else None
    resp = _api(client, "POST", f"/api/user/{login}/key/renew", headers=headers, ok=(200,))
    key = resp.text.strip()
    if len(key) < _MIN_KEY_LEN:
        raise CortexError(f"Cortex returned an implausible api-key (len {len(key)})")
    return key


def create_org(client: httpx.Client, *, name: str, description: str) -> None:
    """Create an organization (Bearer auth). Conflict-tolerant."""
    _api(
        client,
        "POST",
        "/api/organization",
        json_body={"name": name, "description": description, "status": "Active"},
        ok=(200, 201),
        idempotent=True,
    )


def create_user(
    client: httpx.Client, *, login: str, name: str, roles: list[str], organization: str
) -> None:
    """Create an organization user (Bearer auth). Conflict-tolerant."""
    _api(
        client,
        "POST",
        "/api/user",
        json_body={
            "login": login,
            "name": name,
            "roles": roles,
            "organization": organization,
        },
        ok=(200, 201),
        idempotent=True,
    )


def set_user_roles(client: httpx.Client, login: str, roles: list[str]) -> None:
    """PATCH a user's roles (Bearer auth) — idempotent by construction."""
    _api(client, "PATCH", f"/api/user/{login}", json_body={"roles": roles}, ok=(200,))


def set_user_password(client: httpx.Client, login: str, password: str) -> None:
    """Set ``login``'s password (superadmin Bearer; Cortex answers 204).

    Idempotent by nature (re-setting the same password is a no-op
    outcome). This is what lets the student log in to the Cortex UI and
    run an analyzer — the org service user is otherwise API-key only.
    """
    _api(
        client,
        "POST",
        f"/api/user/{login}/password/set",
        json_body={"password": password},
        ok=(200, 204),
    )


def enable_analyzer(
    client: httpx.Client,
    worker_def_id: str,
    *,
    configuration: dict[str, Any] | None = None,
    job_cache: int = 10,
    job_timeout: int = 30,
) -> None:
    """Enable an analyzer for the org (orgadmin Bearer). Conflict-tolerant.

    ``POST /api/organization/analyzer/<workerDefinitionId>`` with the
    config wrapper Cortex 3.1.8 expects (verified live).
    """
    _api(
        client,
        "POST",
        f"/api/organization/analyzer/{worker_def_id}",
        json_body={
            "name": worker_def_id,
            "configuration": configuration or {},
            "jobCache": job_cache,
            "jobTimeout": job_timeout,
        },
        ok=(200, 201),
        idempotent=True,
    )


def _probe_state(base_url: str, transport: httpx.BaseTransport | None) -> str:
    """Classify Cortex: 'fresh' | 'init' (migrated, no users) | 'ready'."""
    client = open_cortex_client(base_url, transport=transport)
    try:
        resp = client.get("/api/user/current")
    finally:
        client.close()
    if resp.status_code == 404 and _USER_INIT_SENTINEL in resp.text:
        return "init"
    if resp.status_code in (200, 401):
        return "ready"  # already has users (initialised)
    return "fresh"  # 520 / not migrated


def bootstrap(
    *,
    base_url: str = _DEFAULT_BASE_URL,
    token_path: Path | None = None,
    transport: httpx.BaseTransport | None = None,
    superadmin_password: str = "wachturm-admin",
    svc_password: str = SVC_PASSWORD,
    abuseipdb_key: str | None = None,
    retries: int = 30,
    sleep: Callable[[float], None] = time.sleep,
) -> Path:
    """Provision Cortex headlessly and write the org service api-key 0600.

    Idempotent. If the token already authenticates, returns immediately
    (no key rotation, no churn). Otherwise it migrates/creates only what
    is missing (conflict-tolerant), (re)mints the service key, and
    enables the analyzers.
    """
    dest = token_path if token_path is not None else _DEFAULT_TOKEN_PATH

    # Fast skip: a present, still-valid token means Cortex is done.
    if dest.exists():
        try:
            verify_api_key(base_url, dest.read_text().strip(), transport=transport)
            return dest
        except CortexError:
            pass  # stale/invalid -> re-establish below

    state = _probe_state(base_url, transport)
    if state == "fresh":
        migrate(base_url, transport=transport)
        wait_user_init(base_url, transport=transport, retries=retries, sleep=sleep)
        state = "init"
    if state == "init":
        init_client = open_cortex_client(base_url, transport=transport)
        try:
            create_superadmin(
                init_client,
                login=SUPERADMIN_LOGIN,
                name="Wachturm Admin",
                password=superadmin_password,
            )
        finally:
            init_client.close()

    sess, csrf = session_login(
        base_url, user=SUPERADMIN_LOGIN, password=superadmin_password, transport=transport
    )
    try:
        admin_key = _renew_key(sess, SUPERADMIN_LOGIN, csrf=csrf)
    finally:
        sess.close()

    admin = open_cortex_client(base_url, api_key=admin_key, transport=transport)
    try:
        create_org(admin, name=ORG_NAME, description="Wachturm SOC lab")
        create_user(
            admin,
            login=SVC_LOGIN,
            name="Wachturm Service",
            roles=SVC_ROLES,
            organization=ORG_NAME,
        )
        set_user_roles(admin, SVC_LOGIN, SVC_ROLES)  # ensure roles on re-run
        set_user_password(admin, SVC_LOGIN, svc_password)  # Cortex UI login
        svc_key = _renew_key(admin, SVC_LOGIN)
    finally:
        admin.close()

    write_token_file(svc_key, path=dest)

    svc = open_cortex_client(base_url, api_key=svc_key, transport=transport)
    try:
        for analyzer in KEYLESS_ANALYZERS:
            enable_analyzer(svc, analyzer)
        if abuseipdb_key:
            enable_analyzer(
                svc, ABUSEIPDB_ANALYZER, configuration={"key": abuseipdb_key, "days": 30}
            )
    finally:
        svc.close()

    verify_api_key(base_url, svc_key, transport=transport)
    return dest
