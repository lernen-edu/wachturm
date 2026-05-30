# vic-web — Wachturm victim: nginx web server (Ubuntu 22.04 + Wazuh agent).
# Reuses the SM2-proven victim pattern (see images/victim-jump): Wazuh
# agent 4.9.2-1 from the OFFICIAL apt repo at build time (§1.6), runtime
# sealed, password-less authd auto-enrollment. Role software: nginx
# (serves benign web hits for noise + web-app scenarios later).
FROM ubuntu:22.04

ARG WAZUH_MANAGER=wazuh-manager
ARG WAZUH_AGENT_VERSION=4.9.2-1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        nginx ca-certificates curl gnupg procps \
 && install -m 0755 -d /usr/share/keyrings \
 && curl -fsSL https://packages.wazuh.com/key/GPG-KEY-WAZUH \
      | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" \
      > /etc/apt/sources.list.d/wazuh.list \
 && apt-get update \
 && WAZUH_MANAGER="${WAZUH_MANAGER}" apt-get install -y \
        wazuh-agent="${WAZUH_AGENT_VERSION}" \
 && apt-mark hold wazuh-agent \
 && rm -rf /var/lib/apt/lists/*

# Copy the whole html tree (index.html + health) so noise-gen's benign
# GET /health returns 200, not a 404 (a 404 stream from one source IP
# trips Wazuh 31151 web_scan/recon — exactly the scanner shape the
# noise-gen contract forbids).
COPY html/ /var/www/html/
COPY --chmod=0755 entrypoint.sh /entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]
