# vic-jump — Wachturm victim: SSH jump host (Ubuntu 22.04 + Wazuh agent).
#
# Role: an SSH-reachable target on the sealed victims network (SCN-001
# SSH brute force, lateral-movement scenarios, ...).
#
# The Wazuh agent is installed at BUILD time from Wazuh's OFFICIAL apt
# repo, version-pinned to 4.9.2-1 to MATCH wazuh/wazuh-manager:4.9.2
# (agent and manager versions must match). Build has network; runtime is
# sealed (victims network is internal:true). This is the AGENTS.md §1.6
# build-time-fetch / runtime-sealed pattern — same as Suricata and the
# cert tool. Image builds for the host arch natively (arm64 here; the
# Wazuh repo serves arm64 + amd64), so victims are NOT emulated.
FROM ubuntu:22.04

ARG WAZUH_MANAGER=wazuh-manager
ARG WAZUH_AGENT_VERSION=4.9.2-1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        openssh-server rsyslog ca-certificates curl gnupg procps \
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
 && mkdir -p /var/run/sshd \
 # Lab-only login so sshd is usable; scenario-specific target users are
 # created by the scenario runner's setup step, not baked here.
 && useradd -m -s /bin/bash analyst && echo 'analyst:analyst' | chpasswd \
 # The Wazuh agent's packaged ossec.conf monitors only dpkg.log +
 # active-responses.log — NOT /var/log/auth.log. Without this the sshd
 # brute-force detection chain (rules 5716/5720/5715) never fires even
 # though rsyslog writes syslog-format events there. Wazuh concatenates
 # multiple <ossec_config> roots, so append one rather than editing the
 # packaged config in place.
 && printf '%s\n' \
      '<ossec_config>' \
      '  <localfile>' \
      '    <log_format>syslog</log_format>' \
      '    <location>/var/log/auth.log</location>' \
      '  </localfile>' \
      '</ossec_config>' >> /var/ossec/etc/ossec.conf

COPY --chmod=0755 entrypoint.sh /entrypoint.sh
EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]
