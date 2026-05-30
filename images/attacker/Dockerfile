# atk-kali — Wachturm attacker (Debian + offensive tooling + Atomic Red
# Team atomics). Despite the name it is Debian-based (lean, reproducible)
# rather than the Kali metapackage; the scenario tooling needed for
# Phase 1 (nmap, hydra, curl, sshpass) is a few pinned Debian packages.
#
# Provenance (AGENTS image-provenance / pin-versions; THIRD_PARTY.md):
#   * Base pinned by digest.
#   * Atomic Red Team is NOT redistributed in this repo: it is fetched
#     at IMAGE-BUILD time from the official redcanaryco/atomic-red-team
#     repo, pinned to an exact commit SHA, sparse-checked-out to the
#     `atomics/` library only, with .git stripped. The runtime is
#     sealed (atk-kali sits on `attack`+`victims`, both internal:true —
#     zero host/internet egress), so the fetch MUST happen at build.
#
# The container is a long-lived `sleep infinity` target; scenarios drive
# it host-side via `docker exec` (the runner, SM5). It deliberately has
# no mgmt/host network — egress isolation is proven empirically in SM4.

# ----- ART fetch stage (needs git + network at BUILD only) -----------
FROM debian:12-slim@sha256:0104b334637a5f19aa9c983a91b54c89887c0984081f2068983107a6f6c21eeb AS art-fetch

ARG ART_REPO=https://github.com/redcanaryco/atomic-red-team.git
# Pin: redcanaryco/atomic-red-team @ master HEAD as of 2026-05-12.
ARG ART_SHA=37400ed636536ef87a36c9b4ef4ac49564ba6b06
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
# Blobless, no-checkout clone then sparse-checkout ONLY atomics/ at the
# pinned SHA (validated sequence — --depth=1 cannot reach an arbitrary
# SHA, so a blobless full-history clone is used). .git is stripped so
# the final image carries the atomics library and nothing else.
RUN git clone --filter=blob:none --no-checkout "${ART_REPO}" /opt/atomic-red-team \
 && cd /opt/atomic-red-team \
 && git sparse-checkout set --no-cone atomics \
 && git checkout "${ART_SHA}" \
 && test -d /opt/atomic-red-team/atomics \
 && rm -rf /opt/atomic-red-team/.git

# ----- final attacker image ------------------------------------------
FROM debian:12-slim@sha256:0104b334637a5f19aa9c983a91b54c89887c0984081f2068983107a6f6c21eeb

LABEL org.wachturm.art.repo="https://github.com/redcanaryco/atomic-red-team" \
      org.wachturm.art.sha="37400ed636536ef87a36c9b4ef4ac49564ba6b06" \
      org.wachturm.art.license="MIT"

ENV DEBIAN_FRONTEND=noninteractive
# Offensive tooling for the Phase-1 scenarios: nmap (recon), hydra
# (credential attacks), curl + sshpass (web/ssh interaction), plus
# python3/bash for ART atomic execution and netcat/iproute2 for the
# SM4 egress-isolation proof. Base digest is the version anchor
# (consistent with the victim images' established pinning approach).
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        nmap hydra curl sshpass openssh-client ca-certificates \
        python3 bash netcat-openbsd iproute2 iputils-ping \
 && rm -rf /var/lib/apt/lists/*

COPY --from=art-fetch /opt/atomic-red-team/atomics /opt/atomic-red-team/atomics

# Seeded wordlists for credential scenarios. wachturm-easy.txt ends with
# the SCN-001 target password (8 wrong guesses + the real one at line 9)
# so hydra produces a deterministic 8-failures-then-success burst that
# fires Wazuh 5760/5763/40112 within the scenario window.
COPY wordlists/ /opt/wordlists/

# Long-lived target; the runner drives attacks via `docker exec`.
# (compose also sets `command: sleep infinity`; kept consistent here so
# the image is correct when run outside compose.)
CMD ["sleep", "infinity"]
