# Wachturm derived cert generator — sealed-runtime variant of the
# official wazuh/wazuh-certs-generator:0.0.2.
#
# WHY THIS EXISTS: the stock 0.0.2 entrypoint downloads
# wazuh-certs-tool.sh from packages.wazuh.com at RUNTIME. Wachturm runs
# every Docker network internal:true (P1 — sealed lab, zero egress, no
# exceptions), so that runtime download cannot happen and the stock
# image exits 1 ("tool does not exist in any bucket"). We vendor the
# EXACT pinned tool at BUILD time (build has network; runtime does not)
# and patch ONLY the download block. Everything else is upstream-
# verbatim, so we still use Wazuh's own cert flow. Same build-time-fetch
# / runtime-sealed principle as AGENTS.md §1.6 (cf. Suricata).
FROM wazuh/wazuh-certs-generator:0.0.4

# The exact file the stock 0.0.2 entrypoint would have fetched from
# https://packages.wazuh.com/4.8/wazuh-certs-tool.sh, pinned by SHA256
# so a silent upstream change cannot alter our TLS bootstrap
# (AGENTS.md §1.5/§1.6). Refresh deliberately via Dependabot/manual bump.
ADD --chmod=0700 \
    --checksum=sha256:acd4fb48c9646904069d81ed9c67f849cf910ab5eb127e051fe9db1dae068874 \
    https://packages.wazuh.com/4.8/wazuh-certs-tool.sh /wazuh-certs-tool.sh

COPY --chmod=0700 entrypoint-offline.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
