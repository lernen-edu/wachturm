#!/bin/sh
# Wachturm IRIS web-TLS one-shot. Idempotent — like images/wazuh-certs-
# generator: skip when a COMPLETE cert set already exists so repeated
# `make up` / `docker compose up` (which gate this via
# service_completed_successfully) keep succeeding; `make reset` wipes
# the iris-web-certs volume, so a fresh lab regenerates. A partial set
# from a crashed run (one file missing or empty) falls through to a
# clean regenerate rather than shipping broken TLS.
set -eu

CERT_DIR=/certs
CRT="$CERT_DIR/iris_cert.pem"
KEY="$CERT_DIR/iris_key.pem"

if [ -s "$CRT" ] && [ -s "$KEY" ]; then
  echo "iris web cert already present in $CERT_DIR — skipping (idempotent)."
  exit 0
fi

mkdir -p "$CERT_DIR"
# Self-signed, loopback only. 10y so a long-lived lab volume never
# expires mid-course. CN + SAN cover the only ways the IRIS UI is ever
# reached (AGENTS.md §6.1 loopback rule); iris-nginx service name is
# included for completeness.
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$KEY" -out "$CRT" -days 3650 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,DNS:iris-nginx,IP:127.0.0.1"

# 0644 on BOTH: this is an intentionally non-secret, throwaway,
# self-signed loopback key — the same sealed-lab posture as the Wazuh
# demo TLS material (SECURITY.md). Readable perms avoid an nginx
# uid/gid "permission denied" rabbit hole for zero confidentiality gain.
chmod 0644 "$CRT" "$KEY"
echo "generated self-signed IRIS web cert (CN=localhost) in $CERT_DIR"
