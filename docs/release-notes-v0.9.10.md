# Wachturm v0.9.10 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.10 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.9

Two fixes for unreliable container startup, particularly on arm64 macOS hosts
running Wazuh and Cortex under amd64 emulation:

- **Increased `--wait-timeout` values** (`Makefile`). `make up` increased from
  600 s to 1200 s; `make up-casemgmt` increased from 900 s to 1800 s. The
  prior values were calibrated for native amd64; under arm64 emulation
  OpenSearch (Wazuh indexer) can take 5–10 minutes to initialise. The timeout
  only fires when something is genuinely broken — on a healthy host `--wait`
  exits as soon as the last service becomes healthy regardless of the limit.

- **Increased service `start_period` values** (`docker-compose.yml`). The grace
  period before health checks begin counting was raised for the services that
  are slow under emulation:

  | Service | Before | After | Max total |
  |---|---|---|---|
  | wazuh-indexer | 120 s | 300 s | 660 s |
  | wazuh-manager | 120 s | 300 s | 660 s |
  | wazuh-dashboard | 120 s | 300 s | 660 s |
  | iris-app | 180 s | 360 s | 960 s |
  | cortex-es | 60 s | 180 s | 660 s |

- **`make install` target added** (`Makefile`). Creates `.venv` and installs the
  runner package so that `make up-casemgmt`'s Python bootstrap steps
  (`iris-bootstrap`, `cortex-bootstrap`) work on a fresh clone without
  requiring a manual `pip install`. `make up-casemgmt` also auto-creates the
  venv if it does not exist.

Everything else is identical to v0.9.9 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
