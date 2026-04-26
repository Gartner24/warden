# Data Flow

Source: `deliverables/warden-architecture.tex` (ADR-01, sections on internal queues and WebSocket dispatch)

## Inter-subsystem (air only)

The two subsystems never share a socket, serial line, or any digital bus during an attack. All communication is via 802.11 frames broadcast over the 2.4 GHz channel (ADR-01).

```
Attacker Panel --> [HTTP/JSON] --> ESP32 API REST (192.168.4.1:80)
ESP32                          --> [802.11 frames] --> air
panda0 (monitor mode)          --> [frame capture] --> Detector
Detector                       --> [asyncio.Queue] --> FastAPI main thread
FastAPI                        --> [WebSocket]     --> Defender Panel (browser)
```

## Attacker side

1. Operator laptop joins `WARDEN_CONTROL` (WPA2-PSK, channel 1, `192.168.4.x`).
2. Attacker Panel sends JSON payloads to `POST /attack/*` on the ESP32 REST API.
3. ESP32 Controlador de Cadena drives the phase sequence; each module emits frames over the 2.4 GHz radio.
4. Evil Twin AP (`10.0.0.1`) serves the captive portal page and accepts a victim POST; credentials are logged to the credentials store (in-memory, volatile).

## Detector side

1. Scapy `sniff()` runs on `panda0` locked to the target channel; alternatively reads from a PCAP file.
2. Each captured frame is handed to the Despachador, which routes by frame type/subtype to the matching analyzer.
3. Analyzers use sliding time windows (no ML - ADR-04); alerts are emitted as structured events to an `asyncio.Queue`.
4. The FastAPI main thread drains the queue and broadcasts JSON events to all connected WebSocket clients.
5. Defender Panel renders alerts in real time; operators can reset the session via `POST /api/session/reset`.

## Key network addresses

| Segment | Range | Owner |
|---|---|---|
| `WARDEN_CONTROL` | `192.168.4.0/24` | ESP32 control AP |
| Evil Twin AP | `10.0.0.0/24` | ESP32 attack AP |
| Defender Panel | `127.0.0.1:8000` | Detector FastAPI server |
