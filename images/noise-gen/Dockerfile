# noise-gen — benign ambient-activity generator (Wachturm SM4).
#
# Base pinned by digest (AGENTS image-provenance / pin-versions). Same
# debian:12-slim lineage as the attacker image to avoid a second base.
# Only an SSH client + curl are needed: noise-gen drives *benign* SSH
# logins and HTTP GETs against the victims so the SOC has realistic
# background traffic. It sits on the sealed `victims` network only
# (no egress) with a fixed pinned IP that SM5 scenarios exclude.
#
# Implements images/noise-gen/README.md (the binding design contract).
FROM debian:12-slim@sha256:2749ca60ffb3c42de053229d7967d292d7dad1067936b38995da0bbfb96c4c23

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        python3 openssh-client sshpass curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --chmod=0755 noise.py /usr/local/bin/noise.py

# Unbuffered so `make noise-start` logs (and the SM4 zero-TP event
# floor) are visible in real time.
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/usr/local/bin/noise.py"]
