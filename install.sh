#!/bin/bash
# Sets up Omarchy → Monkeytype theme sync for Google Chrome (per user, no sudo).
#
#   ./install.sh              register the helper with Chrome and open chrome://extensions
#   ./install.sh --uninstall  remove the registration
#
# Safe to re-run. Re-run it if you move this folder.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_NAME="com.github.omarchy_monkeytype"
# Fixed by the "key" in extension/manifest.json.
EXTENSION_ID="igefhcdbihoeokjllcahmkkdhglhnpki"
HOST_SCRIPT="$ROOT/host/omarchy_monkeytype_host.py"
EXTENSION_DIR="$ROOT/extension"
TARGET_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/google-chrome/NativeMessagingHosts"
TARGET="$TARGET_DIR/$HOST_NAME.json"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33mwarning:\033[0m %s\n' "$*"; }

if [[ ${1:-} == "--uninstall" ]]; then
  rm -f "$TARGET"
  echo "Removed $TARGET"
  echo "Remove the extension itself in chrome://extensions."
  exit 0
fi

# --- checks (warnings only, nothing here blocks the install) ---------------
if ! python3 -c 'import sys, tomllib; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
  warn "Python 3.11+ is required (python3 not found or too old)."
fi
chrome=""
for c in google-chrome-stable google-chrome; do
  command -v "$c" >/dev/null && { chrome=$c; break; }
done
[[ -n $chrome ]] || warn "Google Chrome not found."
[[ -f ${XDG_STATE_HOME:-$HOME/.local/state}/omarchy/current/theme.name ]] \
  || warn "No current Omarchy theme found; the sync starts working once one is set."

# --- register the native messaging host -------------------------------------
chmod +x "$HOST_SCRIPT" "$ROOT"/scripts/*.py
mkdir -p "$TARGET_DIR"
cat > "$TARGET" <<EOF
{
  "name": "$HOST_NAME",
  "description": "Omarchy to Monkeytype theme sync",
  "path": "$HOST_SCRIPT",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXTENSION_ID/"]
}
EOF
echo "Registered helper: $TARGET"

# --- load the extension (the one manual step) -------------------------------
copied=""
if command -v wl-copy >/dev/null && echo -n "$EXTENSION_DIR" | wl-copy 2>/dev/null; then
  copied=" (path is in your clipboard)"
fi

echo
bold "Last step, once per machine:"
echo "  1. In chrome://extensions turn on 'Developer mode' (top right)"
echo "  2. Click 'Load unpacked' and pick$copied:"
echo "       $EXTENSION_DIR"
echo "     In the file dialog, press Ctrl+L and paste the path."
echo
echo "Already loaded? Then you're done; the theme updates on the next Omarchy switch."

if [[ -n $chrome && ${NO_OPEN:-} != 1 ]]; then
  "$chrome" chrome://extensions >/dev/null 2>&1 &
  disown
fi
