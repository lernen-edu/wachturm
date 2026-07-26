# suricata — Wachturm NIDS (Ubuntu 22.04 + Suricata from OISF's OFFICIAL
# apt PPA). Per the locked P3 decision + AGENTS §1.6: no first-party
# Suricata image exists, so we build from the upstream project's official
# package repo (oisf/suricata-stable), version-pinned, at build time;
# runtime is sealed. Native arch (arm64 here; the PPA serves both).
#
# Suricata's packaged default /etc/suricata/suricata.yaml already enables
# EVE JSON to /var/log/suricata/eve.json — we use that (don't fight the
# config). eve.json is shared to the Wazuh manager via the suricata-eve
# volume; the manager ingests it (Wazuh ships Suricata decoders/rules).
FROM ubuntu:22.04

# NOTE: a Launchpad PPA keeps only the LATEST build per series, so an exact
# pin here goes stale the moment OISF publishes a new one -- apt then fails
# with `Version '<pinned>' for 'suricata' was not found` and the whole core
# profile stops building. When that happens, bump this to the current jammy
# version (ubuntu:22.04 == jammy) rather than unpinning:
#
#   curl -sL https://ppa.launchpadcontent.net/oisf/suricata-stable/ubuntu/\
#   dists/jammy/main/binary-amd64/Packages.gz | gunzip \
#     | awk '/^Package: suricata$/{f=1} f&&/^Version:/{print $2; exit}'
ARG SURICATA_VERSION=1:8.0.6-0ubuntu2
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        software-properties-common ca-certificates curl gnupg procps \
 && add-apt-repository -y ppa:oisf/suricata-stable \
 && apt-get update \
 && apt-get install -y suricata="${SURICATA_VERSION}" \
 && apt-mark hold suricata \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/log/suricata

# Scenario-driven EVE alert injection (BUILD_ORDER Phase 3a):
# a bridge-sidecar Suricata cannot capture peer unicast, so network
# scenarios emit the EVE alert their simulated traffic would have
# produced; Wazuh ingests eve.json unchanged. python3 is already present
# (pulled by the suricata package / suricata-update).
COPY --chmod=0755 emit-eve.py /usr/local/bin/wachturm-emit-eve
COPY --chmod=0755 entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
