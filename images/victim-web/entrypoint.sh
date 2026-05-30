#!/bin/bash
# vic-web entrypoint: nginx + Wazuh agent (auto-enrolls via authd on
# first start), then foreground tailing the agent log. Same pattern as
# vic-jump (SM2-proven).
set -euo pipefail

MANAGER="${WAZUH_MANAGER:-wazuh-manager}"
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

nginx               # serves /var/www/html (master process backgrounds)
/var/ossec/bin/wazuh-control start

echo "vic-web: nginx + wazuh-agent started; auto-enrolling to ${MANAGER}"
exec tail -F /var/ossec/logs/ossec.log
