# Module: Detector

Source: `deliverables/warden-architecture.tex` lines 237-249, 391-454

Runtime: Python 3.10+ / Scapy 2.5+

## Responsibilities

Captures 802.11 management frames from a monitor-mode adapter (or PCAP file), routes each frame to the appropriate heuristic analyzer, and emits structured alerts when an attack phase or full chain is detected.

## Pipeline

```
Capturador de Frames
  |-- LiveCapture   (Scapy sniff() on panda0, channel-locked)
  `-- PcapCapture   (Scapy rdpcap())
      |
      v
  Despachador  (routes by frame type/subtype)
      |-- Analizador Beacon Flood  -> D-01: unique beacons/s in sliding window
      |-- Analizador Deauth        -> D-02: deauth count to protected BSSID in window
      |-- Analizador Evil Twin     -> D-03: duplicate SSID with new BSSID
      `-- Correlador de Cadena     -> D-07: all three phases within time window
          |
          v
      Reporte / Alertas  (stdout + asyncio.Queue -> WebSocket)
```

## Source layout (planned)

```
src/detector/
|-- main.py                  CLI entry point (live mode)
|-- capture/
|   |-- live_capture.py
|   `-- pcap_capture.py
|-- analyzers/
|   |-- beacon_flood.py
|   |-- deauth.py
|   |-- evil_twin.py
|   `-- correlator.py
`-- web/                     Defender Panel server (see defender-panel.md)
    |-- server.py
    |-- websocket_manager.py
    |-- routes.py
    `-- static/
```

## CLI usage

```bash
# Live mode
python3 detector.py --iface panda0 --channel 6 --bssid <BSSID> --ssid LAB_WARDEN_UTP

# Offline PCAP mode
python3 detector.py --pcap captures/session.pcap --bssid <BSSID> --ssid LAB_WARDEN_UTP
```

## Detection objectives

| ID | Phase | Heuristic |
|---|---|---|
| D-01 | Beacon Flood | Anomalous unique-beacons-per-second rate |
| D-02 | Deauthentication | Deauth frame count to protected BSSID in window |
| D-03 | Evil Twin | Duplicate SSID with a BSSID different from the protected one |
| D-07 | Full chain | Temporal correlation of D-01 + D-02 + D-03 |

No machine learning (ADR-04).
