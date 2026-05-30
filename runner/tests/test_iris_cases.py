"""TDD for the IRIS case + IOC API added to wachturm.integrations.iris
(P2-M3). Contract grounded against the running v2.4.20 instance and its
own marshmallow source; the HTTP boundary is an httpx.MockTransport so
real client code runs with no lab.
"""

import httpx
import pytest

from wachturm.integrations.iris import (
    IrisError,
    add_ioc,
    create_case,
    ioc_type_id,
    open_iris_client,
)
from wachturm.integrations.observable_extractor import Observable


def _client(handler: object) -> httpx.Client:
    return open_iris_client(
        "https://iris-nginx:8443",
        "k" * 40,
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
    )


def test_create_case_posts_required_fields_and_returns_id() -> None:
    seen: list[httpx.Request] = []

    def h(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, json={"status": "success", "data": {"case_id": 42}})

    cid = create_case(
        _client(h), name="brute force on vic-jump", description="ssh brute", soc_id="w-1"
    )
    assert cid == 42
    assert seen[0].url.path == "/manage/cases/add"
    body = httpx.Request("POST", "x", content=seen[0].content).read()
    assert b"case_name" in body and b"case_customer" in body and b"case_soc_id" in body


def test_create_case_raises_on_error_status() -> None:
    def h(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "error", "message": "bad"})

    with pytest.raises(IrisError):
        create_case(_client(h), name="n", description="d", soc_id="s")


def test_add_ioc_posts_with_cid_query_and_body() -> None:
    seen: list[httpx.Request] = []

    def h(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, json={"status": "success", "data": {"ioc_id": 7}})

    add_ioc(_client(h), 42, value="10.50.10.250", type_id=79, description="attacker")
    assert seen[0].url.path == "/case/ioc/add"
    assert seen[0].url.params.get("cid") == "42"
    body = httpx.Request("POST", "x", content=seen[0].content).read()
    assert b"ioc_value" in body and b"ioc_type_id" in body and b"ioc_tlp_id" in body


def test_add_ioc_raises_on_error() -> None:
    def h(req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(IrisError):
        add_ioc(_client(h), 1, value="x", type_id=79)


def test_ioc_type_id_grounded_mapping() -> None:
    # ids verified live against IRIS v2.4.20 /manage/ioc-types/list
    assert ioc_type_id(Observable("ip", "1.2.3.4", "source")) == 79  # ip-src
    assert ioc_type_id(Observable("ip", "1.2.3.4", "target")) == 77  # ip-dst
    assert ioc_type_id(Observable("hostname", "h", "target")) == 69
    assert ioc_type_id(Observable("username", "u", "target")) == 3  # account
    assert ioc_type_id(Observable("url", "http://x", "observed")) == 141
    assert ioc_type_id(Observable("domain", "x.test", "observed")) == 20
    assert ioc_type_id(Observable("file_hash", "a" * 32, "observed")) == 90  # md5
    assert ioc_type_id(Observable("file_hash", "a" * 40, "observed")) == 111  # sha1
    assert ioc_type_id(Observable("file_hash", "a" * 64, "observed")) == 113  # sha256


def test_ioc_type_id_unmappable_raises() -> None:
    with pytest.raises(ValueError):
        ioc_type_id(Observable("file_hash", "tooshort", "observed"))
