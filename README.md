# WARDEN

**Wireless Attack Reproduction and Detection Environment**

Academic WiFi security project for UTP. WARDEN is a dual-subsystem lab that reproduces a three-phase WiFi attack chain (Beacon Flood -> Deauthentication -> Evil Twin with captive portal) using an ESP32, and detects the same chain in real time using a Python/Scapy sensor paired with a FastAPI dashboard. An in-firmware Ethical Validator restricts all offensive operations to lab-owned BSSIDs and MACs.

> **Academic / lab use only.** See [`deliverables/warden-fundamentos.tex`](deliverables/warden-fundamentos.tex) for the full ethical and legal scope.

---

## Repository layout

```
warden/
|-- README.md
|-- .gitignore
|-- deliverables/          # Academic LaTeX deliverables (Vision, SRS, SAD, Threat Model, ...)
|-- docs/                  # Dev-facing markdown documentation
|   |-- architecture.md
|   |-- data-flow.md
|   |-- lab-setup.md
|   |-- threat-model.md
|   |-- use-cases.md
|   |-- conventions.md
|   |-- modules/
|   |-- adr/
|   `-- api/
|-- src/                   # Source code (created as subsystems are implemented)
|   |-- attacker/          # ESP32 firmware (C++ / Arduino-ESP32)
|   |-- attacker-panel/    # Static HTML/JS panel for the attack operator
|   `-- detector/          # Python detector + FastAPI defender panel
|-- captures/              # Reference PCAPs for offline analysis (gitignored content)
`-- reports/               # Per-session lab reports (gitignored content)
```

---

## Subsystems

| Subsystem | Runtime | Responsibility |
|---|---|---|
| [Attacker firmware](docs/modules/attacker-firmware.md) | ESP32 / C++ Arduino-ESP32 | Executes Beacon Flood, Deauth, and Evil Twin phases; enforces the Ethical Validator |
| [Attacker Panel](docs/modules/attacker-panel.md) | HTML / vanilla JS / Tailwind CDN | Browser UI for the attack operator; talks to the ESP32 REST API over `WARDEN_CONTROL` WiFi |
| [Detector](docs/modules/detector.md) | Python 3.10+ / Scapy 2.5+ | Captures 802.11 frames, runs three heuristic analyzers, correlates into a chain alert |
| [Defender Panel](docs/modules/defender-panel.md) | FastAPI 0.110+ / Uvicorn | Serves the real-time detection dashboard; pushes alerts via WebSocket |

---

## Quickstart

### Attacker firmware (ESP32)

1. Open `src/attacker/` in Arduino IDE 2.x with the Arduino-ESP32 2.0+ board package installed.
2. Install required libraries from the Arduino Library Manager: `ESPAsyncWebServer`, `AsyncTCP`, `ArduinoJson` (see [`docs/lab-setup.md`](docs/lab-setup.md) for details).
3. Flash via USB (115200 baud).
4. After boot the ESP32 exposes `WARDEN_CONTROL` AP (WPA2-PSK `warden-control-pwd`, `192.168.4.1`).

### Attacker Panel

```bash
cd src/attacker-panel
python3 -m http.server 8080
# Open http://localhost:8080 in a browser joined to WARDEN_CONTROL
```

### Detector + Defender Panel

```bash
cd src/detector
pip install -r requirements.txt

# Live capture mode
python3 detector.py --iface panda0 --channel 6 --bssid <LAB_BSSID> --ssid LAB_WARDEN_UTP

# Offline PCAP mode
python3 detector.py --pcap captures/session.pcap --bssid <LAB_BSSID> --ssid LAB_WARDEN_UTP

# Defender Panel (web dashboard on http://localhost:8000)
uvicorn warden.detector.web.server:app --host 127.0.0.1 --port 8000
```

---

## Hardware

| Component | Purpose |
|---|---|
| ESP32-WROOM-32 (4 MB flash, 520 KB RAM) | Offensive subsystem MCU |
| Panda Wireless PAU0B AC600 (MediaTek MT7610U, driver `mt76x0u`) | Monitor-mode USB adapter for the detector |
| Lab WiFi router (SSID `LAB_WARDEN_UTP`, no internet, channel 6) | Simulated victim AP |
| Redmi Note 7 (MIUI 12.5) | Primary victim device |
| Dell Latitude E6220 (Ubuntu Server 22.04.5 LTS) | Secondary victim device |

See [`docs/lab-setup.md`](docs/lab-setup.md) for the full setup procedure.

---

## Documentation

- **Dev docs:** [`docs/`](docs/README.md) - architecture, modules, ADRs, API reference, conventions.
- **Academic deliverables:** [`deliverables/`](deliverables/) - formal UTP submission (Vision, SRS, SAD, Threat Model, Use Cases, etc.) built with `pdflatex`.

---

## License

TBD
