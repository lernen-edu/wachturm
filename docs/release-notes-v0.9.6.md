# Wachturm v0.9.6 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.6 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.5

- **Suricata image updated to 8.0.5** (`images/suricata/Dockerfile`).
  Version `1:8.0.4-0ubuntu1` was superseded and removed from the OISF PPA
  for Ubuntu 22.04 arm64, causing `make up-casemgmt` to fail with
  `E: Version '1:8.0.4-0ubuntu1' for 'suricata' was not found`.
  Pinned to `1:8.0.5-0ubuntu2`, which is the current PPA release for both
  arm64 and amd64.

Everything else is identical to v0.9.5 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
