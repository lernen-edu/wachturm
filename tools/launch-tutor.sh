#!/usr/bin/env bash
#
# launch-tutor.sh — `make tutor` (P3a-3c).
#
# Opens the Wachturm Socratic tutor in a DEDICATED terminal window: it
# detects an available agentic CLI and a terminal emulator, then starts
# the agent in the repo root with the wachturm-tutor skill auto-loaded.
# The student keeps their original terminal for `make` and their browser
# for Wazuh/IRIS/Cortex (the tutor is a coach in its own window — it
# never drives their tools; see skills/wachturm-tutor/SKILL.md).
#
# Agent selection:    detect installed CLIs from {claude, codex, gemini,
#                     opencode, pi}; if several are installed, the student
#                     picks from a menu (primary path). Non-interactive
#                     override (secondary): WACHTURM_TUTOR_AGENT=<cmd> or
#                     `make tutor AGENT=<cmd>`. --dry-run / non-TTY callers
#                     never prompt — they take the first detected agent.
# Terminal detection: macOS `open -a Terminal` · Linux `gnome-terminal`
#                     / `x-terminal-emulator` · Windows Terminal `wt`.
# No terminal launcher  -> in-place launch + a visible warning.
# No agent at all       -> actionable error, exit 1.
#
#   --dry-run   print the resolved agent/terminal/command and exit 0
#               (the test contract — no window is opened). Examples:
#                 $ bash tools/launch-tutor.sh --dry-run
#                   agent=claude  terminal=macos-terminal  ...
#                 $ WACHTURM_TUTOR_AGENT=codex bash tools/launch-tutor.sh --dry-run
#                   agent=codex   ...
#
# Cross-platform note: the macOS path is verified on this project's dev
# host. The Linux and Windows-Terminal branches are constructed to spec
# but are UNTESTED here (documented in PHASE2/▶ release notes).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

# ── 1. detect installed agents, then resolve which one to use ────────
# Known agentic CLIs, in preference order (the menu order and the
# non-interactive default). all five take the bootstrap prompt
# as a positional arg and open interactively EXCEPT opencode, whose TUI
# has no initial-prompt flag (it launches bare and the student pastes the
# prompt). Invocations were confirmed via each CLI's --help on this dev
# host; the per-agent launch command is built in section 1a below.
_KNOWN_AGENTS=(claude codex gemini opencode pi)
DETECTED=()
for _a in "${_KNOWN_AGENTS[@]}"; do
  if command -v "$_a" >/dev/null 2>&1; then DETECTED+=("$_a"); fi
done

# When several are installed, the student picks from a menu. EOF / no
# choice falls back to the first detected so the launcher never hangs.
choose_agent() {                       # echoes the chosen agent to stdout
  printf 'Multiple coding agents detected. Which should run the Wachturm tutor?\n' >&2
  local PS3='Enter a number: ' _c
  select _c in "${DETECTED[@]}"; do
    if [[ -n "$_c" ]]; then printf '%s\n' "$_c"; return 0; fi
    printf 'Pick a number from the list.\n' >&2
  done
  printf '%s\n' "${DETECTED[0]}"
}

if [[ -n "${WACHTURM_TUTOR_AGENT:-}" ]]; then
  AGENT="$WACHTURM_TUTOR_AGENT"                        # explicit override (secondary)
elif [[ ${#DETECTED[@]} -eq 0 ]]; then
  AGENT=""                                            # none found -> error below
elif [[ ${#DETECTED[@]} -eq 1 ]]; then
  AGENT="${DETECTED[0]}"                              # only one -> no menu
elif [[ "$DRY_RUN" == "1" && "${WACHTURM_TUTOR_FORCE_MENU:-}" != "1" ]]; then
  AGENT="${DETECTED[0]}"                              # dry-run never prompts
elif [[ -t 0 || "${WACHTURM_TUTOR_FORCE_MENU:-}" == "1" ]]; then
  AGENT="$(choose_agent)"                             # interactive menu (primary)
else
  AGENT="${DETECTED[0]}"                              # non-TTY fallback
fi

# The tutor skill lives in-repo; both claude and codex accept an opening
# prompt argument, so point the agent at the skill file and let it adopt
# it. (Agent-agnostic: anything that reads files + takes a first prompt.)
TUTOR_PROMPT="You are the Wachturm Tutor. Read skills/wachturm-tutor/SKILL.md \
in this repository and adopt it fully as your operating instructions, then \
follow its start-of-session decision tree. Do not act as a general assistant."

# ── 1a. per-agent invocation ─────────────────────────────────────────
# claude/codex/gemini/pi take the bootstrap prompt as a positional arg
# and open interactively (verified via each CLI's --help on this dev
# host). opencode's TUI has no initial-prompt flag — its positional is a
# project path and `run` is non-interactive — so it launches bare and the
# student pastes the prompt.
AGENT_NEEDS_PASTE=0
if [[ "$AGENT" == "opencode" ]]; then
  AGENT_CMD="$AGENT"; AGENT_NEEDS_PASTE=1
elif [[ -n "$AGENT" ]]; then
  AGENT_CMD="$AGENT $(printf '%q' "$TUTOR_PROMPT")"
else
  AGENT_CMD=""
fi

# ── 2. resolve a terminal launcher ───────────────────────────────────
OS="$(uname -s 2>/dev/null || echo unknown)"
if [[ "$OS" == "Darwin" ]] && command -v open >/dev/null 2>&1; then
  TERMINAL="macos-terminal"
elif command -v gnome-terminal >/dev/null 2>&1; then
  TERMINAL="gnome-terminal"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
  TERMINAL="x-terminal-emulator"
elif command -v wt.exe >/dev/null 2>&1 || command -v wt >/dev/null 2>&1; then
  TERMINAL="windows-terminal"
else
  TERMINAL=""
fi

# ── 3. dry-run: print the plan, open nothing ─────────────────────────
if [[ "$DRY_RUN" == "1" ]]; then
  echo "agent=${AGENT:-<none>}"
  echo "detected=$(IFS=,; echo "${DETECTED[*]:-<none>}")"
  echo "terminal=${TERMINAL:-<none-inplace-fallback>}"
  echo "repo=$REPO_ROOT"
  if [[ "$AGENT_NEEDS_PASTE" == "1" ]]; then
    echo "command=${AGENT}   (interactive; no initial-prompt flag — paste the bootstrap prompt)"
  else
    echo "command=${AGENT:-<none>} \"<wachturm-tutor bootstrap prompt>\""
  fi
  exit 0
fi

# ── 4. no agent — actionable failure ─────────────────────────────────
if [[ -z "$AGENT" ]]; then
  echo "make tutor: no agentic CLI found." >&2
  echo "  Install Claude Code ('claude') or Codex ('codex')," >&2
  echo "  or set WACHTURM_TUTOR_AGENT=<your-agent-command>." >&2
  exit 1
fi

SUMMARY="Tutor launched in new window. Keep this terminal for \`make\` commands; \
use your browser for Wazuh/IRIS/Cortex."

# ── 5. launch in a dedicated window (or fall back in-place) ──────────
echo "Launching the Wachturm tutor with: $AGENT"
if [[ "$AGENT_NEEDS_PASTE" == "1" ]]; then
  printf '  opencode has no "start with a prompt" option. When its window opens,\n  paste this one line to start the tutor:\n\n    %s\n\n' "$TUTOR_PROMPT"
fi
case "$TERMINAL" in
  macos-terminal)
    launcher="$(mktemp -t wachturm-tutor).command"
    cat >"$launcher" <<EOF
#!/bin/bash
cd "$REPO_ROOT" || exit 1
exec $AGENT_CMD
EOF
    chmod +x "$launcher"
    open -a Terminal "$launcher"
    echo "$SUMMARY"
    ;;
  gnome-terminal)
    gnome-terminal --working-directory="$REPO_ROOT" -- \
      bash -lc "$AGENT_CMD; exec bash"
    echo "$SUMMARY"
    ;;
  x-terminal-emulator)
    x-terminal-emulator -e bash -lc \
      "cd '$REPO_ROOT' && $AGENT_CMD; exec bash" &
    echo "$SUMMARY"
    ;;
  windows-terminal)
    WT_BIN="$(command -v wt.exe || command -v wt)"
    "$WT_BIN" new-tab -d "$REPO_ROOT" bash -lc "$AGENT_CMD" &
    echo "$SUMMARY"
    ;;
  *)
    echo "WARNING: no terminal launcher detected — starting the tutor IN PLACE." >&2
    echo "  Ideally run 'make tutor' where a new window can open, so this" >&2
    echo "  terminal stays free for 'make' commands." >&2
    cd "$REPO_ROOT"
    exec $AGENT_CMD
    ;;
esac
