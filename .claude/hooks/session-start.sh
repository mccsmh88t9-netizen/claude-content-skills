#!/bin/bash
# Installs the repo's skills into ~/.claude/skills/ for Claude Code cloud sessions.
set -euo pipefail

# Only run in Claude Code cloud sessions; local users install via /plugin or install.sh
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# Copying ~54 small directories is fast, so run every time to stay in sync with the checkout.
# Send installer output to stderr so it does not end up in the session context.
bash ./install.sh >&2
