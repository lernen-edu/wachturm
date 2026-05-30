#!/bin/bash
# vic-jump entrypoint.
#
# Starts sshd + the Wazuh agent. On first start there is no client.keys,
# so the agent AUTO-ENROLLS with the manager via authd (the manager runs
# password-less authd — <disabled>no</disabled>, see
# config/wazuh/wazuh_cluster/wazuh_manager.conf). Then stay foreground
# tailing the agent log so the container lives and logs are visible.
set -euo pipefail

MANAGER="${WAZUH_MANAGER:-wazuh-manager}"

# Re-assert the manager address at runtime (covers a compose env that
# differs from the build ARG; idempotent).
if [ -f /var/ossec/etc/ossec.conf ]; then
  sed -i "s|<address>[^<]*</address>|<address>${MANAGER}</address>|" \
      /var/ossec/etc/ossec.conf || true
  # Wachturm: disable CIS SCA. Its very wide JSON results overflow the
  # manager analysisd JSON-decoder field cap ("Too many fields for JSON
  # decoder") in volume and can crash analysisd; no scenario teaches
  # configuration assessment. SCA-scoped + idempotent. Mirrors the
  # manager-side disable in config/wazuh/.../wazuh_manager.conf.
  sed -i '/<sca>/,/<\/sca>/ s|<enabled>yes</enabled>|<enabled>no</enabled>|' \
      /var/ossec/etc/ossec.conf || true
fi

mkdir -p /var/run/sshd
# This minimal image has no init system. Start rsyslog in the
# foreground (backgrounded by the shell) BEFORE sshd so sshd's default
# AUTH facility is routed — via stock Ubuntu /etc/rsyslog.d config — to
# /var/log/auth.log in proper SYSLOG format. This matters: `sshd -E`
# writes sshd's *native* format which Wazuh's sshd decoder does NOT
# match (proven with wazuh-logtest: bare -E line -> "No decoder
# matched"; syslog-prefixed line -> rule 5716/5720/5715). The Wazuh
# agent monitors /var/log/auth.log (see Dockerfile) — that is the
# SCN-001 detection chain.
rsyslogd -n &
/usr/sbin/sshd

# First start with no client.keys -> auto-enroll via authd, then connect.
/var/ossec/bin/wazuh-control start

echo "vic-jump: sshd + wazuh-agent started; auto-enrolling to ${MANAGER}"
exec tail -F /var/ossec/logs/ossec.log
