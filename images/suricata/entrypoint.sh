#!/bin/bash
# suricata entrypoint. Captures on all interfaces (the container is
# attached to the victims + mgmt bridges) and writes EVE JSON to
# /var/log/suricata/eve.json (the suricata-eve volume the Wazuh manager
# reads). Uses Suricata's packaged default config (EVE already enabled).
set -euo pipefail

# Update rules best-effort at start (sealed lab -> may be offline; the
# package ships a working ruleset, so failure here is non-fatal).
suricata-update --no-test 2>/dev/null || \
  echo "suricata: rule update skipped (sealed lab); using packaged ruleset"

mkdir -p /var/log/suricata

# Wachturm: drop the `stats` event type from the EVE-log output.
#
# Why: Suricata's `stats` EVE records are ~1097 fields each and are
# emitted every `stats.interval` (8s) forever. The Wazuh manager
# ingests eve.json through its JSON decoder, whose field cap is
# analysisd.decoder_order_size (max 1024, default 256). 1097 > 1024, so
# EVERY stats record triggers "wazuh-analysisd: ERROR: Too many fields
# for JSON decoder"; in volume this degrades/crashes analysisd and real
# scenario alerts are silently dropped (root cause of the WS3d
# intermittent lab failure; the other wide-JSON source, CIS SCA, is
# disabled in config/wazuh/.../wazuh_manager.conf +
# images/victim-*/entrypoint.sh).
#
# How: the EVE-log `types:` list is what selects which events reach
# eve.json (Suricata docs: an absent type is simply not logged). We
# remove the `- stats:` list item and its nested block from the stock
# suricata.yaml. The global `stats:` engine stays ENABLED (default) --
# disabling it makes the eve-log.stats sub-module fail to initialise
# ("unable to initialize sub-module eve-log.stats") and Suricata
# crash-loops. stats.log is still written but Wazuh never reads it
# (only eve.json is a manager localfile). `stats` is Suricata's own
# performance telemetry: zero security value, consumed by no scenario
# and not by observable_extractor (alert events only); the alert path
# (the only EVE type Wachturm uses) is untouched.
#
# Structural (indent-based) edit, not a line-count/comment match: drop
# the `- stats:` item line and every following line indented deeper
# than it, stopping at the next sibling/dedent. Validated against the
# version-pinned stock yaml before baking.
SURICATA_YAML=/etc/suricata/suricata.yaml
if grep -qE '^[[:space:]]*-[[:space:]]*stats:' "$SURICATA_YAML"; then
  awk '
    !skip && /^[[:space:]]*-[[:space:]]*stats:[[:space:]]*$/ {
      match($0, /^[ ]*/); base=RLENGTH; skip=1; next
    }
    skip {
      if ($0 ~ /^[[:space:]]*$/) next                 # blank: still inside block
      match($0, /^[ ]*/)
      if (RLENGTH > base) next                          # deeper: part of stats block
      skip=0                                            # dedented: block ended
    }
    { print }
  ' "$SURICATA_YAML" > "${SURICATA_YAML}.tmp" && mv "${SURICATA_YAML}.tmp" "$SURICATA_YAML"
  echo "suricata: removed eve-log 'stats' type (analysisd JSON-decoder overflow fix)"
fi

# Capture on ALL attached interfaces (the container sits on the victims +
# mgmt bridges). Suricata's default Linux capture is AF_PACKET, which
# CANNOT bind the `any` pseudo-device ("af-packet: any: failed to find
# interface: No such device"). libpcap *does* support the Linux `any`
# device, so we explicitly select pcap live mode with `--pcap=any`.
# (`-i any` would route to AF_PACKET and crash-loop.) EVE output path is
# overridden onto the shared suricata-eve volume the Wazuh manager reads.
echo "suricata: starting NIDS on all interfaces (libpcap any); EVE -> /var/log/suricata/eve.json"
exec suricata --pcap=any \
  --set outputs.1.eve-log.filename=/var/log/suricata/eve.json
