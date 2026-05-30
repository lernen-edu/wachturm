#!/bin/bash
# Wazuh Docker Copyright (C) 2017, Wazuh Inc. (License GPLv2)
#
# Wachturm offline variant of the official wazuh-certs-generator:0.0.2
# /entrypoint.sh. There are THREE Wachturm deviations, all ABOVE the
# "upstream-verbatim" marker below:
#   1. Tool acquisition: upstream curls wazuh-certs-tool.sh from
#      packages.wazuh.com at runtime — impossible on Wachturm's sealed
#      internal:true networks. We vendor that exact pinned tool at
#      image-build time (see Dockerfile).
#   2. Idempotency guard: the upstream tool's `-A` is non-idempotent
#      (aborts exit 1 if its working dir exists), which would break a
#      repeated `make up`. We skip generation when a complete cert set
#      already exists. See the guard block for the full rationale.
#   3. root-ca-manager copy moved before chmod: the upstream flow copies
#      root-ca-manager.{pem,key} AFTER chmod -R 500 /certificates. On
#      Linux native Docker, container root bypasses the mode bit. On
#      macOS via Colima/virtiofs the chmod propagates to the host
#      filesystem and the copy silently fails, leaving root-ca-manager.pem
#      absent and blocking make up-casemgmt. We move the copy before the
#      chmod and restore write permission before overwriting any prior
#      partial cert set.
# EVERYTHING BELOW the upstream-verbatim marker is Wazuh's official
# cert-generation flow, except for deviation 3 in the copy/chmod block.

CERT_TOOL=wazuh-certs-tool.sh

## Tool is vendored into the image at build time (sealed lab, no runtime
## egress — P1). No download; just verify it is present.
if [ ! -f "/$CERT_TOOL" ]; then
  echo "ERROR: vendored /$CERT_TOOL missing from image (build problem)"
  echo "ERROR: certificates were not created"
  exit 1
fi
echo "Using build-time vendored $CERT_TOOL (sealed lab; zero runtime egress)"

# ----- Wachturm idempotency guard (NOT upstream) --------------------
# The official wazuh-certs-tool.sh `-A` is non-idempotent: it aborts
# (exit 1, "Directory wazuh-certificates already exists") on a second
# invocation. Since this one-shot is gated by
# service_completed_successfully, that exit 1 fails every `docker
# compose up` after the lab's first run — breaking the make
# down/up/reset lifecycle (a Phase-1 DoD requirement). Standard
# cert-init pattern: if a COMPLETE cert set already exists in the
# destination, skip generation and succeed. The check requires every
# expected file present AND non-empty (`-s`) so a partially-written
# set from a crashed prior run falls through to a clean regenerate
# rather than silently shipping broken TLS. `make reset` wipes the
# cert volume, so a fresh slate still generates normally.
CERT_FILES="root-ca.pem root-ca.key root-ca-manager.pem root-ca-manager.key \
admin.pem admin-key.pem wazuh.indexer.pem wazuh.indexer-key.pem \
wazuh.dashboard.pem wazuh.dashboard-key.pem wazuh.manager.pem wazuh.manager-key.pem"
all_present=1
for f in $CERT_FILES; do
  [ -s "/certificates/$f" ] || { all_present=0; break; }
done
if [ "$all_present" -eq 1 ]; then
  echo "Wachturm: complete cert set already present in /certificates/ — skipping generation (idempotent)."
  exit 0
fi
echo "Wachturm: cert set absent/incomplete — generating fresh."
# Upstream `-A` aborts if its internal working dir survived a prior
# crashed run; clear it so the upstream-verbatim flow runs clean.
[ -d /wazuh-certificates ] && rm -rf /wazuh-certificates
# On macOS/Colima virtiofs bind mounts, chmod from a prior run
# propagates to the host and leaves the directory and files non-writable.
# Reset to writable before attempting to overwrite any partial cert set.
chmod u+w /certificates 2>/dev/null || true
chmod u+w /certificates/* 2>/dev/null || true

# ----- upstream-verbatim from here down (official 0.0.2 lines 31-61) -----
cp /config/certs.yml /config.yml

chmod 700 /$CERT_TOOL

##############################################################################
# Creating Cluster certificates
##############################################################################

## Execute cert tool and parsin cert.yml to set UID permissions
source /$CERT_TOOL -A
nodes_server=$( cert_parseYaml /config.yml | grep -E "nodes[_]+server[_]+[0-9]+=" | sed -e 's/nodes__server__[0-9]=//' | sed 's/"//g' )
node_names=($nodes_server)

echo "Moving created certificates to the destination directory"
cp /wazuh-certificates/* /certificates/
# Deviation 3: copy root-ca-manager aliases BEFORE chmod so the write
# succeeds on macOS/Colima virtiofs bind mounts (see header comment).
echo "Setting UID for wazuh manager and worker"
cp /certificates/root-ca.pem /certificates/root-ca-manager.pem
cp /certificates/root-ca.key /certificates/root-ca-manager.key
echo "Changing certificate permissions"
chmod -R 500 /certificates
chmod -R 400 /certificates/*
echo "Setting UID indexer and dashboard"
chown 1000:1000 /certificates/*
chown 999:999 /certificates/root-ca-manager.pem
chown 999:999 /certificates/root-ca-manager.key

for i in ${node_names[@]};
do
  chown 999:999 "/certificates/${i}.pem"
  chown 999:999 "/certificates/${i}-key.pem"
done
