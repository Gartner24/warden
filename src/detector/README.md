# Detector (Python)

Scapy-based 802.11 frame analyzer with FastAPI/WebSocket Defender Panel.

## Run (offline, PCAP mode)
```bash
python3 -m detector.main --pcap tests/fixtures/pcap/chain.pcap \
  --bssid AA:BB:CC:DD:EE:FF --ssid LAB_WARDEN_UTP
```

## References
- Architecture: docs/architecture.md
- Module details: docs/modules/detector.md
- API contract: docs/internal/CANONICAL_API.md
- Constants: docs/internal/CONSTANTS.md
