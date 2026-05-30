# Wachturm v0.9.9 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.9 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.8

Two platform-compatibility fixes for arm64 macOS (Apple Silicon) hosts:

- **`debian:12-slim` digest updated to the current multi-arch manifest list**
  (`images/attacker/Dockerfile`, `images/noise-gen/Dockerfile`). The
  previous pin (`sha256:2749ca60…`) was an amd64-specific manifest that has
  since been removed from the registry. Docker fell back to the cached
  amd64 image and warned that the platform did not match the arm64 host.
  Updated to `sha256:0104b334…`, the current multi-arch manifest list index
  that resolves natively to arm64 on Apple Silicon and amd64 on x86 hosts.

- **`platform: linux/amd64` added for Wazuh and Cortex services**
  (`docker-compose.yml`). Wazuh (indexer, manager, dashboard v4.9.2) and
  Cortex (3.1.8) publish amd64-only images. Without an explicit `platform:`
  directive Docker warns on every arm64 start. The directive silences the
  warning and makes the emulation requirement explicit; on amd64 Linux and
  Windows+WSL2 hosts the images run natively as before.

Everything else is identical to v0.9.8 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
