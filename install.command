#!/bin/sh
# macOS Terminal launcher. Resolves paths with spaces; never downloads code.
set -eu
AFP_INSTALL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.9+ is required. Install Python and run this launcher again."
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "Python 3.9+ is required. No installation was performed."
  exit 1
fi
printf 'Install AFP for [1] Codex, [2] Claude Code, [3] portable export (default 1): '
read -r AFP_TARGET_CHOICE
case "$AFP_TARGET_CHOICE" in
  2) set -- --target claude ;;
  3)
    printf 'Exact destination folder ending in agent-filing-protocol: '
    read -r AFP_PORTABLE_DEST
    set -- --target portable --destination "$AFP_PORTABLE_DEST"
    ;;
  ''|1) set -- --target codex ;;
  *) echo "Unknown choice; no installation performed."; exit 1 ;;
esac
AFP_STATUS=0
python3 "$AFP_INSTALL_ROOT/install.py" "$@" --wizard || AFP_STATUS=$?
printf '\nPress Enter to close. '
read -r AFP_CLOSE || true
exit "$AFP_STATUS"
