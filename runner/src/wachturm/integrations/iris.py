"""DFIR-IRIS API token bootstrap (P2-M1).

IRIS v2.4.x exposes **no** endpoint to mint or fetch an API token: each
user's key is auto-created at user creation and only surfaced in the web
UI. So — per the user-approved Phase-2 decision — the bootstrap reads
the initial administrator's ``api_key`` straight out of the local
``iris-db`` Postgres (we own the DB and creds in this sealed loopback
lab; deterministic, no HTML/CSRF scraping), writes it to
``~/.wachturm/iris.token`` 0600 for the Wazuh→IRIS integration and the
future tutor, then confirms it works with an authenticated
``GET /api/ping``.

The two IO boundaries (``docker exec iris-db psql`` and the IRIS HTTPS
API) are injected — an ``Executor`` callable and an ``httpx`` transport —
so the logic is unit-tested without a running lab, matching the
convention in ``wachturm.cli``.
"""

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from wachturm.integrations.observable_extractor import Observable

# (rc, stdout, stderr); identical shape to wachturm.cli._docker_exec.
Executor = Callable[[list[str], int], tuple[int, str, str]]

# IRIS stores one api_key per user; the initial admin post_init creates
# is row id=1. Keying off id (not the login name, which is the SQL
# reserved word "user" and varies by config) is version-stable.
_ADMIN_KEY_SQL = 'SELECT api_key FROM "user" WHERE id = 1'
_MIN_KEY_LEN = 32  # real keys are ~86 chars; guards empty/garbage reads
_PING_PATH = "/api/ping"
_DEFAULT_TOKEN_PATH = Path.home() / ".wachturm" / "iris.token"
_DEFAULT_BASE_URL = "https://127.0.0.1:9000"  # iris-nginx, loopback only


class IrisError(Exception):
    """A recoverable failure in the IRIS bootstrap (mirrors ScenarioError)."""


def read_admin_api_key(
    execute: Executor,
    *,
    container: str = "iris-db",
    db_user: str = "iris",
    db_name: str = "iris_db",
    timeout: int = 15,
) -> str:
    """Read the initial admin's IRIS api_key from the iris-db Postgres.

    Raises IrisError if psql fails or the value is missing/implausible.
    The key itself is never logged.
    """
    argv = [
        "docker",
        "exec",
        container,
        "psql",
        "-U",
        db_user,
        "-d",
        db_name,
        "-tAc",
        _ADMIN_KEY_SQL,
    ]
    rc, out, err = execute(argv, timeout)
    if rc != 0:
        raise IrisError(f"psql read of IRIS admin api_key failed (rc={rc}): {err.strip()}")
    key = out.strip()
    if not key:
        raise IrisError(
            "IRIS admin api_key is empty — is iris-app post_init complete? "
            "(no user row id=1 in iris-db yet)"
        )
    if len(key) < _MIN_KEY_LEN:
        raise IrisError(
            f"IRIS admin api_key has implausible length {len(key)} "
            f"(< {_MIN_KEY_LEN}); refusing to write a bad token"
        )
    return key


def write_token_file(api_key: str, *, path: Path | None = None) -> Path:
    """Write ``api_key`` to ``path`` (default ~/.wachturm/iris.token).

    The parent dir is created 0700 and the token file 0600 — it is a
    credential for the integration and tutor. Returns the written path.
    """
    dest = path if path is not None else _DEFAULT_TOKEN_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(dest.parent, 0o700)
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(api_key)
    os.chmod(dest, 0o600)  # defensive: O_CREAT mode is umask-masked
    return dest


def open_iris_client(
    base_url: str,
    api_key: str,
    *,
    timeout: float = 15.0,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client:
    """An httpx client preset with the IRIS Bearer auth header.

    iris-nginx serves a self-signed cert (sealed loopback lab), so TLS
    verification is disabled for the real transport — verbatim the M1
    construction. ``transport`` is injected by unit tests.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if transport is not None:
        return httpx.Client(
            base_url=base_url, timeout=timeout, headers=headers, transport=transport
        )
    return httpx.Client(base_url=base_url, timeout=timeout, headers=headers, verify=False)  # noqa: S501


def verify_api_key(
    base_url: str,
    api_key: str,
    *,
    timeout: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> None:
    """Confirm ``api_key`` authenticates against ``GET {base_url}/api/ping``.

    Raises IrisError on any non-200 / non-success response.
    """
    client = open_iris_client(base_url, api_key, timeout=timeout, transport=transport)
    try:
        resp = client.get(_PING_PATH)
    except httpx.HTTPError as exc:
        raise IrisError(f"IRIS {_PING_PATH} unreachable: {exc}") from exc
    finally:
        client.close()
    if resp.status_code != 200:
        raise IrisError(f"IRIS {_PING_PATH} returned HTTP {resp.status_code} (token rejected?)")
    try:
        body: dict[str, Any] = resp.json()
    except ValueError as exc:
        raise IrisError(f"IRIS {_PING_PATH} returned non-JSON body") from exc
    if body.get("status") != "success":
        raise IrisError(f"IRIS {_PING_PATH} unexpected body: {body!r}")


def bootstrap(
    execute: Executor,
    *,
    base_url: str = _DEFAULT_BASE_URL,
    token_path: Path | None = None,
    transport: httpx.BaseTransport | None = None,
    retries: int = 30,
    sleep: Callable[[float], None] = time.sleep,
    container: str = "iris-db",
    db_user: str = "iris",
    db_name: str = "iris_db",
) -> Path:
    """Read the admin key, write the 0600 token, confirm it authenticates.

    The key read happens before the write, so a failed read leaves no
    half-written token. The API may lag the iris-app healthcheck, so the
    ``/api/ping`` confirmation is retried with a capped backoff.
    """
    key = read_admin_api_key(execute, container=container, db_user=db_user, db_name=db_name)
    dest = write_token_file(key, path=token_path)
    for attempt in range(retries):
        try:
            verify_api_key(base_url, key, transport=transport)
            return dest
        except IrisError:
            if attempt == retries - 1:
                raise
            sleep(min(2.0 * (attempt + 1), 10.0))
    return dest  # unreachable (loop returns or raises); satisfies typing


def ioc_type_id(obs: Observable) -> int:
    """Map an Observable to the IRIS numeric ioc_type_id.

    Ids verified live against the running v2.4.20 instance
    (/manage/ioc-types/list). Raises ValueError for an unmappable
    observable so the caller can skip it (partial > none).
    """
    if obs.type == "ip":
        return 79 if obs.role == "source" else 77  # ip-src / ip-dst
    if obs.type == "hostname":
        return 69
    if obs.type == "username":
        return 3  # account
    if obs.type == "url":
        return 141
    if obs.type == "domain":
        return 20
    if obs.type == "file_hash":
        by_len = {32: 90, 40: 111, 64: 113}  # md5 / sha1 / sha256
        try:
            return by_len[len(obs.value)]
        except KeyError as exc:
            raise ValueError(f"unmappable hash length {len(obs.value)}") from exc
    raise ValueError(f"no IRIS ioc type for observable type {obs.type!r}")


def _post_ok(
    client: httpx.Client,
    path: str,
    *,
    json_body: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """POST and return the IRIS ``data`` dict, or raise IrisError."""
    try:
        resp = client.post(path, json=json_body, params=params)
    except httpx.HTTPError as exc:
        raise IrisError(f"IRIS {path} unreachable: {exc}") from exc
    if resp.status_code != 200:
        raise IrisError(f"IRIS {path} returned HTTP {resp.status_code}: {resp.text[:200]}")
    try:
        body: dict[str, Any] = resp.json()
    except ValueError as exc:
        raise IrisError(f"IRIS {path} returned non-JSON body") from exc
    if body.get("status") != "success":
        raise IrisError(f"IRIS {path} error: {body.get('message')!r}")
    data = body.get("data")
    return data if isinstance(data, dict) else {}


def create_case(
    client: httpx.Client,
    *,
    name: str,
    description: str,
    soc_id: str,
    customer_id: int = 1,
    classification_id: int | None = None,
    severity_id: int | None = None,
) -> int:
    """Create an IRIS case (POST /manage/cases/add). Returns the case id.

    Required body grounded against the v2.4.20 CaseSchema read from the
    running image: case_name>=2, case_description>=2, case_soc_id,
    case_customer == an existing Client.client_id (default 1).
    """
    body: dict[str, Any] = {
        "case_name": name,
        "case_description": description,
        "case_soc_id": soc_id,
        "case_customer": customer_id,
    }
    if classification_id is not None:
        body["classification_id"] = classification_id
    if severity_id is not None:
        body["severity_id"] = severity_id
    data = _post_ok(client, "/manage/cases/add", json_body=body)
    case_id = data.get("case_id")
    if not isinstance(case_id, int):
        raise IrisError(f"IRIS cases/add returned no integer case_id: {data!r}")
    return case_id


def add_ioc(
    client: httpx.Client,
    case_id: int,
    *,
    value: str,
    type_id: int,
    tlp_id: int = 2,
    description: str = "",
) -> None:
    """Attach an IOC to a case (POST /case/ioc/add?cid=<case_id>).

    Raises IrisError on failure; the caller logs and continues so one
    bad IOC never aborts the case (partial > none).
    """
    _post_ok(
        client,
        "/case/ioc/add",
        params={"cid": case_id},
        json_body={
            "ioc_value": value,
            "ioc_type_id": type_id,
            "ioc_tlp_id": tlp_id,
            "ioc_description": description or value,
        },
    )
