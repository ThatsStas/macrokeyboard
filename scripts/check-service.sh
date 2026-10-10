#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="macrokeyboard"

echo "=== Macro Keyboard — Service Status ==="

# Check if unit file exists
SERVICE_DEST="$HOME/.config/systemd/user/${SERVICE_NAME}.service"
if [ -f "$SERVICE_DEST" ]; then
    echo "✓ Service unit file installed"
else
    echo "✗ Service unit file not found"
fi

# Check if enabled
if systemctl --user is-enabled "$SERVICE_NAME" > /dev/null 2>&1; then
    echo "✓ Service is enabled (auto-start on login)"
else
    echo "✗ Service is disabled"
fi

# Check if running
if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
    echo "✓ Service is RUNNING"
else
    echo "✗ Service is not running"
fi

# Check udev rule
UDEV_RULE="/etc/udev/rules.d/99-macrokeyboard.rules"
if [ -f "$UDEV_RULE" ]; then
    echo "✓ udev rule installed"
else
    echo "✗ udev rule missing — keyboard access may fail"
    echo "  Run as root:"
    echo "    cp systemd/99-macrokeyboard.rules /etc/udev/rules.d/"
    echo "    udevadm control --reload-rules"
    echo "    udevadm trigger"
fi

# Check group membership
if groups | grep -qw input; then
    echo "✓ User is in the 'input' group"
else
    echo "✗ User not in 'input' group — keyboard access denied"
    echo "  Run: newgrp input   (or log out/in)"
fi

echo ""
echo "Recent logs (last 20 lines):"
echo "---"
journalctl --user -u "$SERVICE_NAME" -n 20 --no-pager 2>/dev/null || echo "(no logs found — service may not have run yet)"
echo "---"
