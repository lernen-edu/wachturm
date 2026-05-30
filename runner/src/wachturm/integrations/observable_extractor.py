"""Extract IOC observables from Wazuh alerts for IRIS (P2-M2).

Wazuh alert field names vary by rule/decoder. This pulls the observable
fields that actually appear in the captured fixtures (data.srcip /
data.dstuser / agent.name|ip / predecoder.hostname) plus the documented
syscheck/data hash & URL fields, and is **defensive by contract**: it
extracts what it can and skips anything it can't, and NEVER raises on a
malformed or unexpected alert shape (Phase-2 risk #2). Bad records
must not break the Wazuh→IRIS pipeline.

The Observable -> IRIS IOC type mapping here is best-effort; the exact
IRIS type ids are validated against the live IRIS API in P2-M3 (same
discipline used to ground the IRIS auth flow in P2-M1).
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Observable:
    """A normalized IOC. ``type`` in {ip, hostname, username, file_hash,
    url, domain}; ``role`` in {source, target, observed}."""

    type: str
    value: str
    role: str


def _clean(value: Any) -> str | None:
    """A non-empty, stripped ``str`` — or ``None`` for anything else."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _dict(obj: Any, key: str) -> dict[str, Any]:
    """``obj[key]`` if it is a dict, else ``{}`` (never raises)."""
    if isinstance(obj, dict):
        sub = obj.get(key)
        if isinstance(sub, dict):
            return sub
    return {}


def extract_observables(alert: Any) -> list[Observable]:
    """Observables from one Wazuh alert. Never raises; ``[]`` if unreadable."""
    if not isinstance(alert, dict):
        return []

    out: list[Observable] = []
    seen: set[Observable] = set()

    def add(otype: str, value: Any, role: str) -> None:
        cleaned = _clean(value)
        if cleaned is None:
            return
        obs = Observable(otype, cleaned, role)
        if obs not in seen:
            seen.add(obs)
            out.append(obs)

    data = _dict(alert, "data")
    agent = _dict(alert, "agent")
    predecoder = _dict(alert, "predecoder")
    syscheck = _dict(alert, "syscheck")

    # network
    add("ip", data.get("srcip"), "source")
    add("ip", data.get("dstip"), "target")
    add("ip", agent.get("ip"), "target")  # the monitored victim host
    # identity
    add("username", data.get("srcuser"), "source")
    add("username", data.get("dstuser"), "target")
    add("username", data.get("user"), "observed")
    # host
    add("hostname", agent.get("name"), "target")
    add("hostname", predecoder.get("hostname"), "target")
    add("hostname", data.get("hostname"), "observed")
    # file hashes (Wazuh FIM/syscheck, plus occasional data.*)
    for source in (syscheck, data):
        for key in ("md5_after", "sha1_after", "sha256_after", "md5", "sha1", "sha256"):
            add("file_hash", source.get(key), "observed")
    # web
    add("url", data.get("url"), "observed")
    add("domain", data.get("domain"), "observed")
    return out


def extract_from_lines(lines: Iterable[str]) -> list[Observable]:
    """Deduplicated observables from JSONL alert lines.

    Undecodable lines, blank lines and non-object JSON are skipped — a
    single bad record never breaks the batch.
    """
    out: list[Observable] = []
    seen: set[Observable] = set()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        try:
            alert = json.loads(line)
        except (ValueError, TypeError):
            continue
        for obs in extract_observables(alert):
            if obs not in seen:
                seen.add(obs)
                out.append(obs)
    return out


def iris_ioc_type(obs: Observable) -> str:
    """Best-effort IRIS IOC type name. P2-M3 validates the real IRIS
    type ids against the running IRIS API before case creation."""
    if obs.type == "ip":
        return "ip-src" if obs.role == "source" else "ip-dst"
    if obs.type == "file_hash":
        return {32: "md5", 40: "sha1", 64: "sha256"}.get(len(obs.value), "hash")
    return {
        "hostname": "hostname",
        "username": "account",
        "url": "url",
        "domain": "domain",
    }.get(obs.type, obs.type)
