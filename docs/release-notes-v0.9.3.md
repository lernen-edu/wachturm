# Wachturm v0.9.3 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.3 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.2

Two bug fixes reported by public evaluators:

- **`make up-casemgmt` arithmetic crash when Docker daemon is not running**
  (`Makefile`). When `docker info` exited non-zero but still printed `0` to
  stdout, the `|| echo 0` fallback fired a second time, leaving `mem` holding
  two lines (`0\n0`). The subsequent `$(( mem / 1073741824 ))` was a bash
  syntax error, aborting the entire make target. Fixed by dropping the
  fallback and adding a regex guard: `[[ "$mem" =~ ^[0-9]+$ ]] || mem=0`.

- **`make doctor` falsely fails the Docker Compose v2 check when the plugin
  is installed to a non-standard path** (`runner/src/wachturm/doctor.py`).
  The check only tried `docker compose version`; if that failed (e.g. the
  plugin landed in `/usr/local/cli-plugins/` which Docker CLI does not scan
  by default), doctor reported a hard blocker even when Compose was present.
  Fixed by falling back to `docker-compose version`: standalone v2 reports
  OK, standalone v1 reports WARN, and FAIL is reserved for when neither
  invocation succeeds.

Everything else is identical to v0.9.2 / v0.9.0 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
