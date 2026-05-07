#!/usr/bin/env bash
# Set up Panda PAU0B (panda0) in monitor mode on channel 6.
# Run as root before starting warden-detector.
set -euo pipefail

IFACE="${1:-panda0}"
CHANNEL="${2:-6}"

echo "[warden] Setting $IFACE to monitor mode on channel $CHANNEL"

# Stop NetworkManager interference
if systemctl is-active NetworkManager >/dev/null 2>&1; then
    nmcli dev set "$IFACE" managed no 2>/dev/null || true
fi

# Bring interface down, set monitor mode
ip link set "$IFACE" down
iw dev "$IFACE" set type monitor
ip link set "$IFACE" up

# Set channel
iw dev "$IFACE" set channel "$CHANNEL"

# Confirm
echo "[warden] Interface info:"
iw dev "$IFACE" info

echo "[warden] $IFACE ready for monitor capture."
