# Wachturm v0.9.4 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.4 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.3

- **`make doctor` now prints the symlink fix when Docker Compose v2 is not
  found** (`runner/src/wachturm/doctor.py`). The FAIL message now includes
  the exact two commands needed to wire the plugin into the directory Docker
  CLI scans by default, so users don't have to search for the fix:

  ```
  FAIL  Docker Compose v2: not found ('docker compose' nor 'docker-compose').
        Fix: mkdir -p ~/.docker/cli-plugins && \
             ln -sf /usr/local/cli-plugins/docker-compose ~/.docker/cli-plugins/docker-compose
  ```

Everything else is identical to v0.9.3 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
