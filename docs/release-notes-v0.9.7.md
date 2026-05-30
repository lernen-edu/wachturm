# Wachturm v0.9.7 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.7 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.6

- **`make doctor` fix hints are now platform-aware** (`runner/src/wachturm/doctor.py`).
  The Compose, BuildKit, daemon-not-reachable, and low-memory messages
  previously showed macOS/Homebrew-specific commands regardless of host OS.
  They now branch on platform:

  | Situation | macOS | Linux | Windows + WSL2 |
  |---|---|---|---|
  | Compose not found | symlink from `/usr/local/cli-plugins/` or `brew install` | `apt install docker-compose-plugin` | enable WSL integration in Docker Desktop |
  | BuildKit not found | `brew install docker-buildx` + symlink | `apt install docker-buildx-plugin` | enable WSL integration in Docker Desktop |
  | Daemon unreachable (Colima) | `colima start` | — | — |
  | Daemon unreachable (no Colima) | Is Docker Desktop running? | `systemctl start docker` | start Docker Desktop + enable WSL integration |
  | Docker memory < 12 GiB | `colima start --memory 14` or Docker Desktop Resources | — | Docker Desktop Resources or `.wslconfig` |

- **Suricata version confirmed available on both arm64 and amd64** — `1:8.0.5-0ubuntu2`
  is present in the OISF PPA for Ubuntu 22.04 on both architectures.

Everything else is identical to v0.9.6 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
