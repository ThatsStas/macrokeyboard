#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="macrokeyboard"

echo "=== Macro Keyboard — Uninstall Service ==="

# 1. Stop the service if running
if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
    echo "Stopping service..."
    systemctl --user stop "$SERVICE_NAME"
else
    echo "Service is not running."
fi

# 2. Check it's actually stopped
sleep 1
if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
    echo "ERROR: Service still running after stop!" >&2
    exit 1
fi
echo "✓ Service stopped"

# 3. Disable (remove auto-start)
echo "Disabling service..."
systemctl --user disable "$SERVICE_NAME"
echo "✓ Service disabled"

# 4. Remove the service file
SERVICE_DEST="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
if [ -f "$SERVICE_DEST" ]; then
    rm -f "$SERVICE_DEST"
    echo "✓ Service file removed"
else
    echo "No service file found at $SERVICE_DEST"
fi

# 5. Reload systemd
systemctl --user daemon-reload

echo ""
echo "✓ Service fully removed."
