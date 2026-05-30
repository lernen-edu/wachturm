# vic-dc — Wachturm victim: fake "Domain Controller" emitting
# Windows-shaped logs (Ubuntu 22.04 + Wazuh agent + Python emitter).
#
# PRD §5 explicitly accepts SYNTHETIC Windows-shaped logs from Linux.
# Reuses the SM2-proven victim pattern (Wazuh agent 4.9.2-1, official
# repo, §1.6, sealed runtime, authd auto-enroll). A small Python script
# writes Sysmon/Security-format JSON events; the agent ships that file
# (log_format json) to the manager. Deep Windows-decoder tuning is
# explicitly OUT of scope for v1 (advisor #6 timebox/fallback) — the
# requirement is "Windows-shaped events reach Wazuh", not perfect parsing.
FROM ubuntu:22.04

ARG WAZUH_MANAGER=wazuh-manager
ARG WAZUH_AGENT_VERSION=4.9.2-1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg procps python3 \
 && install -m 0755 -d /usr/share/keyrings \
 && curl -fsSL https://packages.wazuh.com/key/GPG-KEY-WAZUH \
      | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
      > /etc/apt/sources.list.d/wazuh.list \
 && apt-get update \
 && WAZUH_MANAGER="${WAZUH_MANAGER}" apt-get install -y \
        wazuh-agent="${WAZUH_AGENT_VERSION}" \
 && apt-mark hold wazuh-agent \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/log/win

COPY emit-windows-events.py /usr/local/bin/emit-windows-events.py
COPY --chmod=0755 entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
