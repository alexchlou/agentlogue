#!/bin/sh
# macOS Terminal launcher. Resolves paths with spaces; never downloads code.
set -eu
AFP_INSTALL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.9+ is required. Install Python and run this launcher again."
  exit 1
fi
printf 'Install AFP for [1] Codex, [2] Claude Code, [3] portable export (default 1): '
read -r AFP_TARGET_CHOICE
case "$AFP_TARGET_CHOICE" in
  2) python3 "$AFP_INSTALL_ROOT/install.py" --target claude --wizard ;;
  3)
    printf 'Exact destination folder ending in agent-filing-protocol: '
    read -r AFP_PORTABLE_DEST
    python3 "$AFP_INSTALL_ROOT/install.py" --target portable --destination "$AFP_PORTABLE_DEST" --wizard
    ;;
  ''|1) python3 "$AFP_INSTALL_ROOT/install.py" --target codex --wizard ;;
  *) echo "Unknown choice; no installation performed."; exit 1 ;;
esac
printf '\nPress Enter to close. '
read -r AFP_CLOSE
