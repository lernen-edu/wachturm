#!/bin/bash
# vic-dc entrypoint: add a localfile for the synthetic Windows JSON,
# start the emitter + Wazuh agent (auto-enrolls via authd), then
# foreground tail. Same agent pattern as vic-jump (SM2-proven).
set -euo pipefail

MANAGER="${WAZUH_MANAGER:-wazuh-manager}"
CONF=/var/ossec/etc/ossec.conf

if [ -f "$CONF" ]; then
  sed -i "s|<address>[^<]*</address>|<address>${MANAGER}</address>|" "$CONF" || true
  # Wachturm: disable CIS SCA. Its very wide JSON results overflow the
  # manager analysisd JSON-decoder field cap ("Too many fields for JSON
  # decoder") in volume and can crash analysisd; no scenario teaches
  # configuration assessment. SCA-scoped + idempotent. Mirrors the
  # manager-side disable in config/wazuh/.../wazuh_manager.conf.
  sed -i '/<sca>/,/<\/sca>/ s|<enabled>yes</enabled>|<enabled>no</enabled>|' "$CONF" || true
  # Tell the agent to ship the synthetic Windows JSON (idempotent).
  if ! grep -q '/var/log/win/events.json' "$CONF"; then
    sed -i 's#</ossec_config>#  <localfile>\n    <log_format>json</log_format>\n    <location>/var/log/win/events.json</location>\n  </localfile>\n</ossec_config>#' "$CONF"
  fi
fi

mkdir -p /var/log/win && : > /var/log/win/events.json
python3 /usr/local/bin/emit-windows-events.py &

/var/ossec/bin/wazuh-control start
echo "vic-dc: emitter + wazuh-agent started; auto-enrolling to ${MANAGER}"
exec tail -F /var/ossec/logs/ossec.log
