# Wachturm v0.9.1 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.1 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.0

- **Added: a Windows setup guide** — `docs/student/windows-setup.md`.
  Wachturm is built on macOS and runs the same on Linux; on Windows the
  supported path is **WSL2 + Docker Desktop** (the Linux path, inside
  Windows). The new guide walks a Windows student from a fresh machine to a
  running lab: install WSL2/Ubuntu, set the `.wslconfig` memory, enable
  Docker Desktop's WSL integration, **clone inside WSL2** (for I/O speed and
  to avoid line-ending corruption), then the normal `make` flow in the
  Ubuntu shell with the tool UIs in your Windows browser — plus running the
  tutor across WSL2 tabs, and troubleshooting. It's linked from the student
  README and the root README quickstart, and needs no code changes (it
  rides the existing Linux path).

Everything else is identical to v0.9.0 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
