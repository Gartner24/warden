#!/usr/bin/env bash
# UC-12 offline demo: start detector against chain.pcap, verify 4 alert types appear.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
source .venv/bin/activate 2>/dev/null || source venv/bin/activate

echo "[demo] Generating fixtures if missing..."
[ -f tests/fixtures/pcap/chain.pcap ] || python3 scripts/generate-fixtures.py

echo "[demo] Running detector against chain.pcap..."
export PYTHONPATH="src"
timeout 10 python3 -m detector.main \
    --pcap tests/fixtures/pcap/chain.pcap \
    --bssid AA:BB:CC:DD:EE:FF \
    --ssid LAB_WARDEN_UTP \
    --ventana-corr 120 \
    2>/dev/null | tee /tmp/warden-demo-output.txt

echo ""
echo "[demo] Alert types detected:"
grep -oE 'BEACON_FLOOD|DEAUTH|EVIL_TWIN|CADENA_OFENSIVA' /tmp/warden-demo-output.txt | sort -u

echo "[demo] Done."
