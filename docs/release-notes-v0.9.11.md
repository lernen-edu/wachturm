# Wachturm v0.9.11 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.11 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.10

- **`iris-nginx` marked unhealthy during startup** (`docker-compose.yml`).
  Two related fixes:

  1. **iris-app health check upgraded from TCP-open to HTTP probe.** The
     previous check (`connect_ex` to port 8000) passed as soon as gunicorn
     bound its socket — before workers were ready to serve HTTP. iris-nginx
     would then start (its `depends_on` satisfied), attempt to proxy, and
     immediately get `Connection refused`, exhausting its health-check retries
     before gunicorn finished warming up. The new check does a real HTTP
     request (`curl http://127.0.0.1:8000/`) and only passes when iris-app
     returns a valid response (200 / 301 / 302 / 401 / 403).

  2. **iris-nginx health check overridden with a 60 s `start_period`.** The
     upstream image ships its own `HEALTHCHECK` with no grace period; it can
     exhaust retries during the small window between iris-app passing its TCP
     check and fully serving HTTP. The compose override adds a grace period
     while keeping the same probe (`curl -sk https://127.0.0.1:8443/`).

Everything else is identical to v0.9.10 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
