# Wachturm Wazuh->IRIS watcher (P2-M3).
#
# Always-on: tails the Wazuh manager's alerts.json (mounted read-only
# via the wazuh_logs volume — the M0 share contract) and creates
# DFIR-IRIS cases with extracted observables. The pure pipeline is
# wachturm.integrations.wazuh_to_iris (unit-tested); this image just
# runs the `wachturm wazuh-to-iris` watcher loop.
#
# Build context is the repo root (so the runner package is installable;
# see the root .dockerignore). pip install happens at BUILD time only —
# the runtime is sealed, the same build-time-fetch principle as the
# other Wachturm-built images (AGENTS.md §1.6).
FROM python:3.11-slim
WORKDIR /app
COPY runner/ /app/runner/
RUN pip install --no-cache-dir /app/runner
ENV PYTHONUNBUFFERED=1
# Defaults target the in-container mounts / the mgmt-network IRIS host.
ENTRYPOINT ["wachturm", "wazuh-to-iris"]
