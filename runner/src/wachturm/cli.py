"""Wachturm command-line interface.

The scenario engine internals (schema, step executor, expected-alerts
integrity check) are unit-tested in ``wachturm.scenario`` /
``wachturm.runner``. This module is the thin host-side orchestration
over them plus the unavoidable IO boundary (``docker exec`` and reading
the Wazuh manager's alerts.json); that boundary is exercised
end-to-end by ``make scenario SCN=SCN-001`` (BUILD_ORDER Phase-1 DoD).

Note: this module deliberately does NOT use
``from __future__ import annotations``. PEP 563 stringizes annotations,
which breaks Typer's runtime introspection of ``Annotated[...]``
parameter metadata.
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Annotated, Any

import typer

from wachturm import __version__
from wachturm.doctor import run as run_doctor
from wachturm.hints import load_state as _hint_load_state
from wachturm.hints import next_hint as _next_hint
from wachturm.hints import save_state as _hint_save_state
from wachturm.integrations.cortex import CortexError
from wachturm.integrations.cortex import bootstrap as _cortex_bootstrap
from wachturm.integrations.iris import (
    IrisError,
)
from wachturm.integrations.iris import add_ioc as _iris_add_ioc
from wachturm.integrations.iris import bootstrap as _iris_bootstrap
from wachturm.integrations.iris import create_case as _iris_create_case
from wachturm.integrations.iris import ioc_type_id as _iris_ioc_type_id
from wachturm.integrations.iris import open_iris_client as _iris_open_client
from wachturm.integrations.observable_extractor import Observable
from wachturm.integrations.wazuh_to_iris import DedupKey
from wachturm.integrations.wazuh_to_iris import process as _w2i_process
from wachturm.runner import (
    AlertCheck,
    check_expected_alerts,
    parse_wazuh_timestamp,
    run_plan,
    scenario_state,
)
from wachturm.scenario import ScenarioError, load_scenario
from wachturm.scoring import fetch_latest_closed_case as _fetch_case
from wachturm.scoring import score as _score

app = typer.Typer(
    name="wachturm",
    help="Wachturm — Tier 1 SOC analyst simulator (scenario runner and scoring).",
    no_args_is_help=True,
    add_completion=False,
)

SCENARIOS_DIR = Path(__file__).resolve().parents[3] / "scenarios"
_MANAGER = "wazuh-manager"
_ALERTS = "/var/ossec/logs/alerts/alerts.json"
_DECODE_GRACE_SECONDS = 45
_PORTAL = "wachturm-portal"
_PORTAL_STATE_PATH = "/usr/share/nginx/html/state.json"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"wachturm {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the Wachturm version and exit.",
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Wachturm CLI root."""


@app.command()
def doctor() -> None:
    """Check Docker, Compose, and host resources (Phase 0; real)."""
    raise typer.Exit(code=run_doctor())


def _docker_exec(argv: list[str], timeout: int) -> tuple[int, str, str]:
    """Default executor: run an argv on the host (it begins ``docker exec``)."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return (p.returncode, p.stdout, p.stderr)
    except subprocess.TimeoutExpired:
        return (124, "", f"timeout after {timeout}s")


def _manager_sh(command: str) -> str:
    p = subprocess.run(
        ["docker", "exec", _MANAGER, "sh", "-c", command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return p.stdout.strip()


def _alerts_offset() -> int:
    out = _manager_sh(f"test -f {_ALERTS} && wc -c < {_ALERTS} || echo 0")
    try:
        return int(out)
    except ValueError:
        return 0


def _read_alerts_since(offset: int) -> list[dict[str, Any]]:
    """Read alerts.json appended past ``offset``; normalize to {rule, ts}."""
    raw = _manager_sh(f"tail -c +{offset + 1} {_ALERTS} 2>/dev/null || true")
    out: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = rec.get("timestamp")
        epoch = parse_wazuh_timestamp(ts) if isinstance(ts, str) else 0.0
        out.append({"rule": rec.get("rule", {}), "ts": epoch})
    return out


def _write_portal_state(state: dict[str, Any]) -> None:
    """Best-effort: docker-cp the Phase-1 state snapshot into the portal.

    The unavoidable IO boundary (like ``_manager_sh``), exercised e2e by
    ``make scenario``. NEVER raises and NEVER affects the scenario exit
    code: a stopped/absent portal must not fail a run. The host tempfile
    is chmod 0644 *before* ``docker cp`` (cp preserves source mode) so
    nginx's worker — a different uid than root — can read it; otherwise
    ``/api/state`` would 403. Phase-1 stub only (BUILD_ORDER:155-156).
    """
    tmp = ""
    try:
        fd, tmp = tempfile.mkstemp(prefix="wachturm-state-", suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh)
        os.chmod(tmp, 0o644)
        r = subprocess.run(
            ["docker", "cp", tmp, f"{_PORTAL}:{_PORTAL_STATE_PATH}"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            typer.echo(f"  (portal state not updated: {r.stderr.strip()})", err=True)
    except (OSError, subprocess.SubprocessError) as exc:
        typer.echo(f"  (portal state not updated: {exc})", err=True)
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


def _resolve_scenario(scn: str) -> Path:
    matches = sorted(SCENARIOS_DIR.glob(f"{scn}*.yml"))
    if not matches:
        typer.echo(f"error: no scenario file matching {scn}* in {SCENARIOS_DIR}", err=True)
        raise typer.Exit(code=1)
    return matches[0]


@app.command()
def scenario(scn: Annotated[str, typer.Argument(help="Scenario id, e.g. SCN-001")]) -> None:
    """Run a scenario end-to-end against the running lab (Phase 1)."""
    path = _resolve_scenario(scn)
    try:
        spec = load_scenario(path)
    except ScenarioError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"▶ {spec.id} — {spec.name}")
    started = time.time()
    # Phase-3 live state (BUILD_ORDER:155-156): mark RUNNING up front so
    # the wachturm-tutor, polling /api/state, sees the scenario start —
    # not only its end. Best-effort; never gates the run.
    _write_portal_state(
        scenario_state(
            spec,
            "running",
            started=started,
            hints_used=_hint_load_state(spec.id).revealed,
        )
    )
    snap: dict[str, float | int] = {}

    def _between() -> None:
        # Snapshot AFTER setup, BEFORE steps, so setup noise can't
        # contaminate the expected_alerts window.
        snap["offset"] = _alerts_offset()
        snap["since"] = time.time()
        typer.echo(f"  setup complete; alerts offset={snap['offset']}")

    results = run_plan(
        spec, execute=_docker_exec, sleep=time.sleep, between_setup_and_steps=_between
    )

    failed = False
    for i, r in enumerate(results, 1):
        typer.echo(_step_progress(i, len(results), r.returncode, r.ok))
        if not r.ok:
            failed = True

    checks: list[AlertCheck] | None = None
    if spec.expected_alerts:
        typer.echo(f"  waiting {_DECODE_GRACE_SECONDS}s for Wazuh to decode…")
        time.sleep(_DECODE_GRACE_SECONDS)
        alerts = _read_alerts_since(int(snap.get("offset", 0)))
        ok, checks = check_expected_alerts(
            spec.expected_alerts, alerts, since_ts=float(snap.get("since", 0.0))
        )
        for c in checks:
            mark = "✓" if c.ok else "✗"
            typer.echo(
                f"  {mark} rule {c.rule_id}: saw {c.seen}/{c.required} within {c.timeframe}s"
            )
        # SCENARIO_SCHEMA §5: a missed expected alert is LAB_INTEGRITY,
        # surfaced as a warning — not a student-facing failure.
        typer.echo("LAB_INTEGRITY_OK" if ok else "LAB_INTEGRITY_FAIL")

    # Phase-3 live state: mark COMPLETED, written regardless of pass/fail
    # and BEFORE the failure exit so a failed run is still reflected.
    # Best-effort; never gates the exit code (that keys off step
    # `failed` only). hints_used carries through so the tutor sees the
    # student's hint spend without re-reading the hint file.
    finished = time.time()
    _write_portal_state(
        scenario_state(
            spec,
            "completed",
            started=started,
            finished=finished,
            results=results,
            alert_checks=checks,
            hints_used=_hint_load_state(spec.id).revealed,
        )
    )

    if failed:
        typer.echo("scenario completed with step failures", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"✔ {spec.id} ran end-to-end")


@app.command()
def score(scn: Annotated[str, typer.Argument(help="Scenario id, e.g. SCN-001")]) -> None:
    """Score your closed IRIS case against the scenario answer key (Phase 2).

    Grades the most-recently-closed case (closing a case is your "this
    is my answer" signal) on the SCENARIO_SCHEMA.md §6 rubric. Reads the
    verdict/severity/confidence tags and your case summary; never
    crashes on a missing or still-open case — it tells you what to do.
    """
    path = _resolve_scenario(scn)
    try:
        spec = load_scenario(path)
    except ScenarioError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    token_path = Path.home() / ".wachturm" / "iris.token"
    if not token_path.exists():
        typer.echo(f"error: {token_path} not found — run `make up-casemgmt` first.", err=True)
        raise typer.Exit(code=1)
    client = _iris_open_client("https://127.0.0.1:9000", token_path.read_text().strip())
    try:
        snapshot = _fetch_case(client)
    finally:
        client.close()

    result = _score(
        snapshot,
        spec.answer_key,
        scenario_id=spec.id,
        weights=spec.scoring_weights or None,
        hints_used=_hint_load_state(spec.id).revealed,
    )

    if not result.components:  # no case / not closed — guide, don't crash
        typer.echo(f"▶ {spec.id}: not yet gradable")
        typer.echo(f"  {result.reasoning}")
        raise typer.Exit(code=1)

    typer.echo(f"▶ Scoring {spec.id} — graded IRIS case #{result.graded_case_id}")
    for c in result.components:
        mark = "✓" if c.awarded >= c.possible and c.possible > 0 else " "
        typer.echo(f"  {mark} {c.name:<17}{c.awarded:>5.0f} / {c.possible:<5.0f} {c.detail}")
    pct = (100.0 * result.total / result.possible) if result.possible else 0.0
    typer.echo(f"  {'─' * 44}")
    typer.echo(f"    {'TOTAL':<17}{result.total:>5.0f} / {result.possible:<5.0f} ({pct:.0f}%)")
    typer.echo("\nAnswer-key reasoning:")
    typer.echo(f"  {result.reasoning}")

    # Phase-3 live state: mark SCORED + carry the score so the tutor's
    # post-scenario reflection mode sees it without re-grading.
    _write_portal_state(
        scenario_state(
            spec,
            "scored",
            last_score={
                "total": result.total,
                "possible": result.possible,
                "pct": round(pct),
                "graded_case_id": result.graded_case_id,
            },
            expected_case_id=result.graded_case_id,
            hints_used=_hint_load_state(spec.id).revealed,
        )
    )


@app.command()
def hint(scn: Annotated[str, typer.Argument(help="Scenario id, e.g. SCN-001")]) -> None:
    """Reveal the next un-revealed hint for a scenario (Phase 3a).

    Hints are general -> specific. Each one you reveal costs 5 points
    from your `make score` (SCENARIO_SCHEMA.md §7) — the count is shared
    with the scorer via ~/.wachturm/hints/<SCN>.json, so you cannot
    hint-farm a perfect score.
    """
    path = _resolve_scenario(scn)
    try:
        spec = load_scenario(path)
    except ScenarioError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    total = len(spec.hints)
    text, new_state = _next_hint(spec.hints, _hint_load_state(spec.id))
    if text is None:
        msg = f"▶ {spec.id}: no more hints" + (
            f" — all {total} already revealed (-{int(5 * total)} pts at scoring)."
            if total
            else " — this scenario ships none."
        )
        typer.echo(msg)
        return
    _hint_save_state(new_state)
    typer.echo(f"▶ {spec.id} — hint {new_state.revealed} of {total}  (-5 pts at scoring)")
    typer.echo(f"  {text}")


@app.command()
def validate(
    path: Annotated[str, typer.Argument(help="Path to scenario YAML(s)")] = "scenarios",
) -> None:
    """Validate scenario YAML(s) against the schema + require the trio (Phase 1).

    CI runs this on every push. Each ``SCN-*.yml`` must parse AND have a
    matching ``.brief.md`` and ``.instructor.md`` (SCENARIO_SCHEMA §1).
    """
    target = Path(path)
    files = sorted(target.glob("SCN-*.yml")) if target.is_dir() else [target]
    if not files:
        typer.echo(f"no scenario files found under {target}", err=True)
        raise typer.Exit(code=1)

    failures = 0
    for f in files:
        try:
            spec = load_scenario(f)
        except ScenarioError as exc:
            typer.echo(f"✗ {f.name}: {exc}", err=True)
            failures += 1
            continue
        stem = f.name[: -len(".yml")]
        missing = [
            ext
            for ext in (".brief.md", ".instructor.md")
            if not (f.parent / f"{stem}{ext}").is_file()
        ]
        if missing:
            typer.echo(f"✗ {f.name}: missing trio file(s): {', '.join(missing)}", err=True)
            failures += 1
            continue
        typer.echo(f"✓ {f.name} ({spec.id}, {spec.expected_verdict})")

    if failures:
        typer.echo(f"{failures} scenario(s) failed validation", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"all {len(files)} scenario(s) valid")


# The curriculum teaches difficulties as Beginner/Medium/Advanced; the
# scenario schema stores easy/medium/hard. Accept the student-facing words
# (any capitalization) so `make scenarios FILTER='--difficulty beginner'`
# isn't a silent empty list.
_DIFFICULTY_ALIASES = {"beginner": "easy", "advanced": "hard"}


def _normalize_difficulty(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip().lower()
    return _DIFFICULTY_ALIASES.get(v, v)


def _step_progress(idx: int, total: int, returncode: int, ok: bool) -> str:
    """Student-facing per-step progress line for ``make scenario``.

    Deliberately does NOT include the step's author-written ``description``:
    those describe the actual attack (e.g. "authenticated scan ... all
    fail") and would spoil the verdict the student must derive. Keep this
    structural — index/total + rc + a pass/fail mark — so the no-spoiler
    design (WS0) cannot regress through this line.
    """
    mark = "✓" if ok else "✗"
    return f"  {mark} step {idx}/{total} (rc={returncode})"


@app.command()
def scenarios(
    difficulty: Annotated[
        str | None,
        typer.Option(help="filter: easy|medium|hard (also accepts beginner/advanced)"),
    ] = None,
    verdict: Annotated[
        str | None,
        typer.Option(help="filter: true_positive|false_positive|benign"),
    ] = None,
    category: Annotated[
        str | None, typer.Option(help="case-insensitive substring of the YAML category")
    ] = None,
) -> None:
    """List the scenario library (id / difficulty / verdict / category /
    name), optionally filtered. Backs ``make scenarios`` (BUILD_ORDER §3a)."""
    diff_filter = _normalize_difficulty(difficulty)
    rows: list[tuple[str, str, str, str, str]] = []
    for p in sorted(SCENARIOS_DIR.glob("SCN-*.yml")):
        try:
            s = load_scenario(p)
        except ScenarioError:
            continue
        if diff_filter and s.difficulty != diff_filter:
            continue
        if verdict and s.expected_verdict != verdict:
            continue
        if category and category.lower() not in s.category.lower():
            continue
        rows.append((s.id, s.difficulty, s.expected_verdict, s.category, s.name))
    for sid, diff, verd, cat, name in rows:
        typer.echo(f"{sid:<8} {diff:<7} {verd:<15} {cat:<20} {name}")
    typer.echo(f"\n{len(rows)} scenario(s)")


@app.command("iris-bootstrap")
def iris_bootstrap() -> None:
    """Write ~/.wachturm/iris.token from the running IRIS (Phase 2).

    Reads the initial admin's API key out of iris-db, writes it 0600,
    and confirms it authenticates against IRIS /api/ping. Invoked by
    ``make up-casemgmt``; idempotent and safe to re-run. The key itself
    is never printed.
    """
    try:
        path = _iris_bootstrap(execute=_docker_exec)
    except IrisError as exc:
        typer.echo(f"error: IRIS token bootstrap failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"✔ IRIS API token written {path} (0600); authenticated /api/ping OK")


@app.command("cortex-bootstrap")
def cortex_bootstrap() -> None:
    """Provision Cortex and write ~/.wachturm/cortex.token (Phase 2).

    Headlessly migrates Cortex, creates the superadmin + ``wachturm``
    org + service user, writes the org service api-key 0600, and enables
    the keyless analyzers (plus AbuseIPDB iff ``ABUSEIPDB_API_KEY`` is
    set in the environment). Invoked by ``make up-casemgmt``; idempotent
    and safe to re-run. The key itself is never printed.
    """
    try:
        path = _cortex_bootstrap(abuseipdb_key=os.environ.get("ABUSEIPDB_API_KEY") or None)
    except CortexError as exc:
        typer.echo(f"error: Cortex bootstrap failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"✔ Cortex service api-key written {path} (0600); analyzers enabled")


def _wait_for_token(path: Path, *, retries: int = 120, delay: float = 2.0) -> str:
    """Block until ``path`` holds a non-empty token, then return it.

    `make up-casemgmt` writes the token (iris-bootstrap) AFTER the stack
    is healthy, so the watcher container starts BEFORE it exists. The
    token dir is bind-mounted live, so we just poll.
    """
    for _ in range(retries):
        try:
            text = path.read_text().strip()
            if text:
                return text
        except OSError:
            pass
        time.sleep(delay)
    raise typer.Exit(code=1)


@app.command("wazuh-to-iris")
def wazuh_to_iris(
    alerts_path: Annotated[str, typer.Option(help="Wazuh alerts.json (mounted ro)")] = (
        "/var/ossec/logs/alerts/alerts.json"
    ),
    token_path: Annotated[str, typer.Option(help="IRIS token (mounted ro)")] = (
        "/etc/wachturm/iris.token"
    ),
    base_url: Annotated[str, typer.Option(help="IRIS API base URL")] = "https://iris-nginx:8443",
    poll_interval: Annotated[float, typer.Option(help="Seconds between tails")] = 3.0,
    min_level: Annotated[
        int, typer.Option(envvar="WACHTURM_MIN_LEVEL", help="Min Wazuh rule level")
    ] = 3,
) -> None:
    """Always-on watcher: tail Wazuh alerts.json → create IRIS cases (Phase 2).

    The IO boundary (file tail + IRIS HTTP); the pure pipeline it drives
    is unit-tested in wachturm.integrations.wazuh_to_iris, and this loop
    is e2e-verified by the 90s alert→case DoD. Starts at EOF (only new
    alerts make cases) and never dies on a transient error.
    """
    key = _wait_for_token(Path(token_path))
    client = _iris_open_client(base_url, key)

    def _create(payload: dict[str, str]) -> int:
        return _iris_create_case(
            client,
            name=payload["name"],
            description=payload["description"],
            soc_id=payload["soc_id"],
        )

    def _add(case_id: int, obs: Observable) -> None:
        _iris_add_ioc(
            client,
            case_id,
            value=obs.value,
            type_id=_iris_ioc_type_id(obs),
            description=f"{obs.type}/{obs.role} extracted from a Wazuh alert",
        )

    apath = Path(alerts_path)
    offset = apath.stat().st_size if apath.exists() else 0
    state: dict[DedupKey, tuple[int, float]] = {}
    typer.echo(
        f"wazuh-to-iris watching {apath} from offset {offset}; "
        f"IRIS={base_url} min_level={min_level}"
    )
    while True:
        try:
            if apath.exists():
                size = apath.stat().st_size
                if size < offset:  # rotated/truncated → resync
                    offset = 0
                if size > offset:
                    with apath.open("rb") as fh:
                        fh.seek(offset)
                        chunk = fh.read()
                    offset += len(chunk)
                    lines = chunk.decode("utf-8", "replace").splitlines()
                    created = _w2i_process(
                        lines,
                        create_case=_create,
                        add_ioc=_add,
                        min_level=min_level,
                        state=state,
                    )
                    for cid in created:
                        typer.echo(f"created IRIS case {cid}")
        except Exception as exc:  # noqa: BLE001 - the watcher must never die
            typer.echo(f"watch cycle error (continuing): {exc}", err=True)
        time.sleep(poll_interval)


def main_entrypoint() -> None:
    """Console-script entry point (``wachturm`` / ``python -m wachturm``)."""
    app()


if __name__ == "__main__":
    main_entrypoint()
