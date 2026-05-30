# Wachturm IRIS web-TLS generator — one-shot self-signed cert for the
# iriswebapp_nginx front end (loopback lab; students click through the
# self-signed warning exactly as they do for the Wazuh dashboard).
#
# WHY THIS EXISTS: the pinned iriswebapp_nginx:v2.4.20 image does NOT
# self-generate a cert — it nginx-[emerg]-exits with "cannot load
# certificate /www/certs/" unless a real cert/key is present. Upstream
# iris-web ships an external cert step + a read-only mount; Wachturm
# mirrors its OWN proven pattern instead (cf. images/wazuh-certs-
# generator): a tiny one-shot that openssl-generates the cert into a
# named volume which iris-nginx mounts read-only, gated by
# service_completed_successfully.
#
# SEALED RUNTIME (AGENTS.md §1.6): openssl is installed at BUILD time
# (build has network); the container performs NO runtime package fetch,
# same build-time-fetch / runtime-sealed principle as the Wazuh and
# Suricata images.
FROM alpine:3.21
RUN apk add --no-cache openssl
COPY --chmod=0755 gen-cert.sh /gen-cert.sh
ENTRYPOINT ["/gen-cert.sh"]
