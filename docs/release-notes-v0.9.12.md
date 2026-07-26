# Wachturm v0.9.12 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.12 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.11

Cortex headless bootstrap recovery — `make up-casemgmt` could fail at the
Cortex step with an opaque error:

```
error: Cortex bootstrap failed: Cortex POST /api/login -> HTTP 401: Authentication failure
```

**Root cause.** If Cortex's database carries leftover user state from a
previous or partial run (e.g. interrupted bring-ups while tuning startup
timeouts), the one-time *init window* that lets the bootstrap create its
superadmin is already closed — Cortex's API offers no way to mint a
superadmin once any user exists. The bootstrap then can't authenticate as
its `admin` user and dies. Wiping only the Elasticsearch volume isn't
enough: stale state in the second Cortex volume re-seeds the broken users
on the next bring-up, so **both** Cortex volumes must be cleared.

### Added

- **`make reset-cortex`** — surgically wipes *only* Cortex's state (both the
  `cortex-es-data` and `cortex-data` volumes plus the cached service token)
  and leaves IRIS case work and Wazuh data untouched. This is the supported
  recovery for a wedged Cortex, far less destructive than `make reset` (which
  tears down the entire lab and all volumes). After it runs:

  ```
  make reset-cortex && make up-casemgmt
  ```

### Fixed

- **Actionable bootstrap error** (`runner/src/wachturm/integrations/cortex.py`).
  When Cortex has users but no usable Wachturm superadmin (login fails / init
  window closed), the bootstrap now explains exactly what happened and points
  at the one-command fix (`make reset-cortex && make up-casemgmt`) instead of
  surfacing a bare `HTTP 401: Authentication failure`.

A clean Cortex bootstrap (verified end to end) creates the superadmin, the
`wachturm` org and service user, mints the service api-key, and enables the
two keyless analyzers (`ValidateObservable`, `DShield_lookup`).

Everything else is identical to v0.9.11 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
