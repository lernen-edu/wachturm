# Wachturm v0.9.5 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.5 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.4

Three new `make doctor` pre-flight checks that surface the setup issues
discovered during v0.9.3–v0.9.4 evaluation:

- **Docker daemon reachability** — if `docker info` fails, doctor now detects
  whether Colima is installed but stopped and prints the fix:

  ```
  FAIL  Docker daemon not reachable. Colima is not running.
        Fix: colima start
        For core+casemgmt (~12 GiB needed): colima stop && colima start --memory 14
  ```

- **Docker memory allocation** — when the daemon is reachable, doctor checks
  how much RAM the Docker VM (Colima or Docker Desktop) has been allocated.
  Colima defaults to 2 GiB, which is far short of what the full stack needs:

  ```
  WARN  Docker memory: 2.0 GiB allocated (core+casemgmt needs ~12 GiB).
        Fix: colima stop && colima start --memory 14
  ```

- **Docker BuildKit (buildx)** — `COPY --chmod` in the Dockerfiles requires
  BuildKit. If the `docker-buildx` plugin is missing, doctor now reports a
  blocker and prints the fix:

  ```
  FAIL  Docker BuildKit (buildx): not found.
        Fix: brew install docker-buildx && \
             ln -sf /opt/homebrew/opt/docker-buildx/bin/docker-buildx ~/.docker/cli-plugins/docker-buildx
  ```

Everything else is identical to v0.9.4 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
