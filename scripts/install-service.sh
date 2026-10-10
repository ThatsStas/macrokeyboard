#!/usr/bin/env bash
set -euo pipefail

# Determine project directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_NAME="macrokeyboard"
SERVICE_DEST="$HOME/.config/systemd/user/${SERVICE_NAME}.service"

# Detect python3 path
PYTHON_PATH=""
for p in /usr/bin/python3 /usr/sbin/python3 python3; do
    if [ -x "$p" ]; then
        PYTHON_PATH="$p"
        break
    fi
done
if [ -z "$PYTHON_PATH" ]; then
    echo "ERROR: python3 not found on this system." >&2
    exit 1
fi

echo "=== Macro Keyboard — Install Service ==="
echo ""

# 0. Check for udev rule
UDEV_RULE="/etc/udev/rules.d/99-macrokeyboard.rules"
if [ ! -f "$UDEV_RULE" ]; then
    echo "Installing udev rule to grant keyboard access..."
    if [ "$(id -u)" -eq 0 ]; then
        cat > "$UDEV_RULE" <<'EOF'
# Allow access to input devices for the macro keyboard
SUBSYSTEM=="input", GROUP="input", MODE="0660"
EOF
        udevadm control --reload-rules
        udevadm trigger
        echo "  udev rule installed."
    else
        echo "  WARNING: Not running as root." >&2
        echo "  Install the udev rule manually:" >&2
        echo "    sudo cp systemd/99-macrokeyboard.rules /etc/udev/rules.d/" >&2
        echo "    sudo udevadm control --reload-rules" >&2
        echo "    sudo udevadm trigger" >&2
    fi
else
    echo "✓ udev rule already installed."
fi

# Check if user is in the 'input' group
if ! groups | grep -qw input; then
    echo ""
    echo "⚠ $USER is not in the 'input' group." >&2
    echo "  Without this, the service cannot access the keyboard." >&2
    echo "  Run: newgrp input   (or log out and back in)" >&2
fi

# 1. Install the service file
echo ""
echo "Installing service unit to $SERVICE_DEST..."
mkdir -p "$HOME/.config/systemd/user"
cat > "$SERVICE_DEST" <<EOF
[Unit]
Description=Macro Keyboard — hardware macro keyboard with voice-to-text
After=graphical-session.target dbus-session.service

[Service]
Type=simple
Environment=XDG_RUNTIME_DIR=%t
ExecStart=$PYTHON_PATH $PROJECT_DIR/run_macros.py
Environment=STT_ENDPOINT=http://10.0.0.93:9001/v1/audio/transcriptions
Environment=VOICE_DEVICE=plughw:5,0
Environment=LOG_LEVEL=INFO
Restart=on-failure
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=macrokeyboard

[Install]
WantedBy=default.target
EOF

# 2. Reload systemd user daemon
echo "Reloading systemd user daemon..."
systemctl --user daemon-reload

# 3. Enable (auto-start on login)
echo "Enabling service for auto-start..."
systemctl --user enable "$SERVICE_NAME"

# 4. Start the service
echo "Starting service..."
systemctl --user start "$SERVICE_NAME"

# 5. Wait briefly and check status
echo ""
sleep 2
if systemctl --user is-active "$SERVICE_NAME" > /dev/null 2>&1; then
    echo "✓ Service is RUNNING"
    echo ""
    echo "View logs:  journalctl --user -u $SERVICE_NAME -f"
    echo "Stop it:    systemctl --user stop $SERVICE_NAME"
    echo "Status:     systemctl --user status $SERVICE_NAME"
else
    echo "✗ Service started but is not active!" >&2
    echo ""
    echo "Check logs for errors:"
    echo "  journalctl --user -u $SERVICE_NAME -n 50"
    exit 1
fi

echo ""
echo "Done."
