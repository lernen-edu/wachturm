#!/usr/bin/env bash
#
# gather-state.sh — single-call state gatherer for the Wachturm tutor.
#
# Outputs JSON describing the current state of the Wachturm stack so the
# tutor has everything it needs in one query. Designed to be called by
# the tutor at session start.
#
# Usage:
#   ./gather-state.sh [--iris-token TOKEN] [--cortex-key KEY]
#
# If tokens are not provided, the script falls back to ~/.wachturm/iris.token
# and ~/.wachturm/cortex.token if those exist. Missing tokens degrade
# gracefully — the corresponding section will be omitted from the output.
#
# All errors are reported in the JSON output, not on stderr (so the tutor
# can handle them in a single parse).

set -uo pipefail

IRIS_TOKEN="${IRIS_TOKEN:-}"
CORTEX_KEY="${CORTEX_KEY:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iris-token)  IRIS_TOKEN="$2";  shift 2 ;;
    --cortex-key)  CORTEX_KEY="$2";  shift 2 ;;
    *)             shift ;;
  esac
done

# Token discovery fallback
[[ -z "$IRIS_TOKEN" && -f "$HOME/.wachturm/iris.token" ]]  && IRIS_TOKEN="$(cat "$HOME/.wachturm/iris.token")"
[[ -z "$CORTEX_KEY" && -f "$HOME/.wachturm/cortex.token" ]] && CORTEX_KEY="$(cat "$HOME/.wachturm/cortex.token")"

# ── Stack status ──────────────────────────────────────────────────────
stack_json="{}"
if command -v docker >/dev/null 2>&1; then
  containers="$(docker ps --format '{{.Names}}|{{.Status}}' 2>/dev/null | grep -E '(wazuh|iris|cortex|wachturm|shuffle|misp|suricata|atk|vic|noise)' || true)"
  if [[ -n "$containers" ]]; then
    stack_lines=()
    while IFS='|' read -r name status; do
      [[ -z "$name" ]] && continue
      healthy="false"
      [[ "$status" == *"Up"* ]] && healthy="true"
      stack_lines+=("\"$name\":{\"status\":\"$status\",\"healthy\":$healthy}")
    done <<< "$containers"
    stack_json="{$(IFS=,; echo "${stack_lines[*]}")}"
  fi
fi

# ── Portal state ──────────────────────────────────────────────────────
portal_state="$(curl -sf --max-time 3 http://127.0.0.1:8000/api/state 2>/dev/null || echo '{}')"

# ── IRIS — latest case ────────────────────────────────────────────────
iris_json='{"available":false,"reason":"no_token"}'
if [[ -n "$IRIS_TOKEN" ]]; then
  iris_resp="$(curl -sk --max-time 5 \
    -H "Authorization: Bearer $IRIS_TOKEN" \
    "https://127.0.0.1:9000/manage/cases/list" 2>/dev/null || echo '')"
  if [[ -n "$iris_resp" ]]; then
    iris_json="{\"available\":true,\"cases\":$iris_resp}"
  else
    iris_json='{"available":false,"reason":"api_unreachable"}'
  fi
fi

# ── Cortex — recent jobs ──────────────────────────────────────────────
cortex_json='{"available":false,"reason":"no_token"}'
if [[ -n "$CORTEX_KEY" ]]; then
  cortex_resp="$(curl -s --max-time 5 \
    -H "Authorization: Bearer $CORTEX_KEY" \
    "http://127.0.0.1:9001/api/job?range=0-20" 2>/dev/null || echo '')"
  if [[ -n "$cortex_resp" ]]; then
    cortex_json="{\"available\":true,\"jobs\":$cortex_resp}"
  else
    cortex_json='{"available":false,"reason":"api_unreachable"}'
  fi
fi

# ── Final payload ─────────────────────────────────────────────────────
cat <<EOF
{
  "gathered_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "stack": $stack_json,
  "portal_state": $portal_state,
  "iris": $iris_json,
  "cortex": $cortex_json
}
EOF
