#!/bin/bash
# Registers the native messaging host with Google Chrome (per user, no sudo).
# Re-run it if you move this folder.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_NAME="com.github.omarchy_monkeytype"
# Fixed by the "key" in extension/manifest.json.
EXTENSION_ID="igefhcdbihoeokjllcahmkkdhglhnpki"
HOST_SCRIPT="$ROOT/host/omarchy_monkeytype_host.py"
TARGET_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/google-chrome/NativeMessagingHosts"

chmod +x "$HOST_SCRIPT"
mkdir -p "$TARGET_DIR"
cat > "$TARGET_DIR/$HOST_NAME.json" <<EOF
{
  "name": "$HOST_NAME",
  "description": "Omarchy to Monkeytype theme sync",
  "path": "$HOST_SCRIPT",
  "type": "stdio",
  "allowed_origins": ["chrome-extension://$EXTENSION_ID/"]
}
EOF

echo "Installed $TARGET_DIR/$HOST_NAME.json"
echo
echo "Next: open chrome://extensions, turn on Developer mode,"
echo "click 'Load unpacked' and pick: $ROOT/extension"
