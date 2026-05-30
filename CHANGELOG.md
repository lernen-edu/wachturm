# Changelog

All notable changes to Wachturm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Project documentation: architecture overview, scenario schema, third-party license audit, contributing guide, security policy, and the instructor guide
- Both AI skills: `scenario-author` (for contributors authoring scenarios) and `wachturm-tutor` (Socratic coaching skill for students)
- Portal landing page implementation (HTML/JS/nginx) at `images/portal/`
- Docker Compose scaffold with profiles for `core`, `casemgmt`, `soar`, and `intel`
- GitHub Actions workflows: `ci.yml`, `codeql.yml`, `container-scan.yml`
- Dependabot configuration for pip, github-actions, and Docker ecosystems
- Issue and PR templates at `.github/`
- Apache 2.0 license for code, CC BY-SA 4.0 for scenarios and documentation
- Student curriculum (9 docs in `docs/student/`) and instructor guide
- Scenario taxonomy at `scenarios/_taxonomy.md` (30 planned scenarios across v1.0–v1.2)
- Example instructor doc for SCN-001 SSH brute force

### Notes
- This Unreleased section accumulates work-in-progress changes between releases. Each `v*` tag moves entries from Unreleased into a numbered section below.

## [0.9.9] — public evaluation pre-release

### Fixed
- `debian:12-slim` digest in `attacker` and `noise-gen` Dockerfiles updated from the stale amd64-specific manifest (`sha256:2749ca60…`) to the current multi-arch manifest list (`sha256:0104b334…`). The old digest had been removed from the registry and caused amd64 platform warnings on arm64 hosts.
- Added `platform: linux/amd64` to `wazuh-indexer`, `wazuh-manager`, `wazuh-dashboard`, and `cortex` in `docker-compose.yml`. These upstream images are amd64-only; the explicit directive silences the platform mismatch warning on arm64 hosts and documents the emulation requirement.

## [0.9.8] — public evaluation pre-release

### Fixed
- `make up-casemgmt` failed with `permission denied` on `root-ca-manager.pem` on macOS/Colima. The cert generator's `chmod -R 500 /certificates` propagated to the virtiofs bind mount on the host, making the directory non-writable before the `root-ca-manager.{pem,key}` copies. Fixed by moving those copies before the chmod and adding a write-permission reset at the start of any re-generation.

## [0.9.7] — public evaluation pre-release

### Fixed
- `make doctor` fix hints are now platform-aware. Compose, BuildKit, daemon-not-reachable, and low-memory messages previously showed macOS/Homebrew-specific commands on all platforms. They now branch on macOS, Linux, and Windows+WSL2, giving correct instructions for each.

## [0.9.6] — public evaluation pre-release

### Fixed
- Suricata image pinned to `1:8.0.5-0ubuntu2` (was `1:8.0.4-0ubuntu1`). The 8.0.4 package was removed from the OISF PPA for Ubuntu 22.04 arm64, breaking `make up-casemgmt` with a version-not-found error.

## [0.9.5] — public evaluation pre-release

### Fixed
- `make doctor` now checks Docker daemon reachability; if Colima is installed but stopped it prints `colima start` (and the `--memory 14` variant for the casemgmt stack).
- `make doctor` now checks Docker VM memory allocation and warns when it is below the 12 GiB needed for `core+casemgmt`, with the Colima fix command.
- `make doctor` now checks for the Docker BuildKit plugin (`docker buildx`) and prints the `brew install docker-buildx` fix when missing, preventing the `COPY --chmod` build error.

## [0.9.4] — public evaluation pre-release

### Fixed
- `make doctor` now prints the symlink fix command when Docker Compose v2 is not found, so users with the plugin installed to a non-standard path (e.g. `/usr/local/cli-plugins/`) know exactly how to resolve it.

## [0.9.3] — public evaluation pre-release

### Fixed
- `make up-casemgmt` crashed with a bash arithmetic error when the Docker daemon was not running: `docker info` printed `0` to stdout then exited non-zero, causing `|| echo 0` to fire a second time and leaving `mem` as a two-line string that broke `$(( mem / 1073741824 ))`. Fixed by replacing the fallback with a regex guard.
- `make doctor` falsely reported Docker Compose v2 as missing when the plugin was installed to a non-standard path (e.g. `/usr/local/cli-plugins/`). Fixed by falling back to `docker-compose version` and distinguishing v2 (OK), v1 (WARN), and truly absent (FAIL).

## [0.9.0] — public evaluation pre-release

The complete v1.0 product, published to the public repo so external
evaluators can use it exactly as a student will. **Not yet 1.0.0** — the
v1.0.0 release is gated on independent human testing (external testers + an
educator review), and v0.9.0 is the artifact under evaluation. See
`docs/release-notes-v0.9.0.md`.

### Added (on top of the 0.1.0 scaffold)
- 15 scenarios (8 beginner / 5 medium / 2 advanced; 7 TP / 5 FP / 3 BN), three files each, no-spoiler titles (CI-enforced)
- `make scenario` / `make score` (rubric grading of the closed IRIS case) / `make hint` (progressive, −5 pts each, shared with the scorer) / `make scenarios` (filterable library)
- `make tutor` — Socratic AI tutor that scans for an installed agent (Claude Code / Codex / Gemini CLI / OpenCode / Pi) and lets the student pick; coaches via read-only state, never drives tools or gives answers, and remembers progress across sessions (`~/.wachturm/tutor/`)
- Full student curriculum (`docs/student/`) and instructor guide

### Fixed
- Wazuh `analysisd` wide-JSON flood (CIS SCA + Suricata `stats`) that could silently drop scenario alerts on a long-running lab
- A class of learner-doc and tutor accuracy defects surfaced by own-context persona testing (wrong profile in the walkthrough, the untaught verdict/severity/confidence tag convention, a `make scenario` step-description spoiler leak, and more)

### Notes
- `v1.0.0` remains gated; it publishes as the validated "latest" release only after the human-testing gate passes.

## [0.1.0] — Phase 0 complete (internal)

Pre-public internal milestone. Not promoted to the public repo.

### Added
- Repo skeleton: Makefile stubs, .gitignore, .env.example, pre-commit config
- Python runner package skeleton at `runner/` with `pyproject.toml` and CLI entry point
- CI workflow validating `docker compose config`, runner linting, and tests
- All Phase 0 DoD items met

## [1.0.0] — first public release (planned)

The first public release. Published automatically when the source repo is tagged `v1.0.0`.

### Planned scope
- 15 scenarios (8 beginner, 5 medium, 2 advanced); realistic 7 true-positive / 5 false-positive / 3 benign verdict mix; no-spoiler titles (CI-enforced)
- v1.0 stack: Wazuh (SIEM/EDR/HIDS) + Suricata 8.0 (NIDS) + DFIR-IRIS (case management) + Cortex (enrichment). Attack/benign activity is per-scenario scripted (ART-inspired, not the bundled ART framework). Shuffle (SOAR) and MISP (threat intel) are wired as roadmap profiles for v1.1+, not part of the v1.0 loop.
- Stability hardening: Wazuh `analysisd` JSON-decoder overflow root-caused and fixed (see `docs/release-notes-v1.0.md`)
- Complete student curriculum and instructor guide
- Wachturm Socratic tutor skill, installable in Claude Code or Codex
- Scenario authoring skill for contributors

[Unreleased]: https://github.com/lernen-edu/wachturm/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/lernen-edu/wachturm/releases/tag/v1.0.0
