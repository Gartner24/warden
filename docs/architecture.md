# Architecture

Source: `deliverables/warden-architecture.tex`

WARDEN has two independent subsystems that communicate exclusively over the 802.11 air interface (ADR-01). There is no direct socket, serial, or bus connection between the offensive and defensive sides during an attack.

## Subsystems

| Subsystem | Runtime | Entry point |
|---|---|---|
| Attacker firmware | ESP32 / C++ / Arduino-ESP32 2.0+ | `src/attacker/` |
| Attacker Panel | Static HTML + vanilla JS + Tailwind CDN | `src/attacker-panel/index.html` |
| Detector | Python 3.10+ / Scapy 2.5+ | `src/detector/main.py` |
| Defender Panel | FastAPI 0.110+ / Uvicorn 0.27+ | `src/detector/web/server.py` |

## Module decomposition

### Attacker firmware (`src/attacker/`)

```
Controlador de Cadena
|-- Modulo Beacon Flood
|-- Modulo Deauth
`-- Modulo Evil Twin
    |-- Portal Cautivo
    |-- Servidor DNS local
    `-- Servidor DHCP
Reconocedor
Lookup OUI  (flash-embedded DB ~5 000 entries)
Configuracion
Validador Etico
Interfaz Serial
AP de Control  (WARDEN_CONTROL, 192.168.4.1)
Servidor API REST  (/scan, /clients, /oui-lookup, /attack/*, /config, /credentials, /events)
```

### Detector + Defender Panel (`src/detector/`)

```
Capturador de Frames  (live iface or PCAP)
`-- Despachador
    |-- Analizador Beacon Flood   -> D-01
    |-- Analizador Deauth         -> D-02
    |-- Analizador Evil Twin      -> D-03
    `-- Correlador de Cadena      -> D-07
        `-- Reporte / Alertas
FastAPI server
`-- WebSocket Manager
    `-- Defender Panel (static HTML/JS)
Configuracion  (CLI args)
Manejador de Sesion
```

## Runtime view

1. Operator joins `WARDEN_CONTROL` WiFi on the attacker laptop.
2. Attacker Panel (`192.168.4.1`) configures target BSSID; Ethical Validator confirms.
3. ESP32 executes Beacon Flood -> Deauth -> Evil Twin over 2.4 GHz.
4. Panda adapter (monitor mode, `panda0`, channel 6) feeds frames to the detector on the defender laptop.
5. Detector emits alerts to stdout and pushes events over WebSocket to the Defender Panel at `localhost:8000`.

## Deployment view

```
[Attacker laptop]         [ESP32]              [Air / 2.4 GHz]    [Defender laptop]
 Attacker Panel  <-HTTP-> API REST   --------> 802.11 frames ---> panda0 (monitor)
 browser                  192.168.4.1                              Detector
                                                                   Defender Panel
                                                                   localhost:8000
```

## ADR index

| ADR | Decision |
|---|---|
| [0001](adr/0001-air-only-comms.md) | Inter-subsystem comms exclusively over the air |
| [0002](adr/0002-python-scapy-detector.md) | Python + Scapy for the defensive subsystem |
| [0003](adr/0003-esp32-offensive.md) | ESP32 for the offensive subsystem |
| [0004](adr/0004-no-ml-heuristics.md) | Heuristic rule-based detection, no ML |
| [0005](adr/0005-external-config.md) | External (out-of-code) configuration |
| [0006](adr/0006-ethical-validator-in-firmware.md) | Ethical Validator inside the firmware |
| [0007](adr/0007-hybrid-attacker-panel.md) | Hybrid frontend/API for the Attacker Panel |
| [0008](adr/0008-fastapi-websockets.md) | FastAPI + WebSockets for the Defender Panel |
| [0009](adr/0009-oui-flash-embedded.md) | OUI database embedded in ESP32 flash |
