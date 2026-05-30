# Wachturm v0.9.2 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.2 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.1

- **Hardened the Windows setup guide** (`docs/student/windows-setup.md`)
  after a literal-beginner review, so a first-time Windows user can follow
  it end to end. It now shows how to open PowerShell as Administrator,
  walks through creating `.wslconfig` in Notepad (and avoids the silent
  `.wslconfig.txt` trap that caused mysterious crashes later), makes
  "launch Docker Desktop and wait for the whale icon" explicit, removes a
  double-run of the first scenario at the hand-off to `02-first-shift.md`,
  marks the tutor optional with a concrete install pointer, and adds a
  "Cannot connect to the Docker daemon" troubleshooting entry.

Everything else is identical to v0.9.1 / v0.9.0 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
