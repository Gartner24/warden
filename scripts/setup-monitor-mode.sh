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

# Add a virtual monitor interface (mon0) on the same phy.
# On mt76x0u the converted $IFACE passes zero frames to userspace;
# mon0 works correctly and is used as the actual capture interface.
PHY=$(iw dev "$IFACE" info | awk '/wiphy/{print "phy"$2}')
iw dev mon0 del 2>/dev/null || true
iw phy "$PHY" interface add mon0 type monitor
ip link set mon0 up

# Confirm
echo "[warden] Interface info:"
iw dev "$IFACE" info
iw dev mon0 info

echo "[warden] $IFACE (control) + mon0 (capture) ready."
