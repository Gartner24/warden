# API: Detector FastAPI

Source: `deliverables/warden-architecture.tex` lines 245-246, `deliverables/warden-use-cases.tex` lines 885-910

Base URL: `http://127.0.0.1:8000` (local only by default)

## HTTP endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Serves the Defender Panel HTML |
| GET | `/api/status` | Current session state: running, alert counts, uptime |
| POST | `/api/session/reset` | Clear all analyzer state and counters; restart the session |
| GET | `/api/config` | Read current detection thresholds |
| POST | `/api/config` | Update detection thresholds at runtime |
| POST | `/api/detector/start` | Start the detector; body: `{ iface, channel, bssid_protegido, ssid_protegido, umbrales }` |
| POST | `/api/detector/stop` | Stop the running detector |

## WebSocket

`ws://127.0.0.1:8000/ws`

The server pushes JSON events to all connected clients. The browser does not send messages over this socket.

### Backend → Frontend messages

**On connect (`init`):**
```json
{
  "tipo": "init",
  "alertas_recientes": [],
  "estado": "conectado"
}
```

**New alert:**
```json
{
  "tipo": "alerta",
  "datos": {
    "timestamp": "2026-04-25T14:23:01",
    "severidad": "ALERT",
    "tipo": "BEACON_FLOOD",
    "mensaje": "Tasa anomala de beacons: 87.4 BSSIDs unicos/s",
    "detalles": { "bssids_unicos": 437, "ventana_seg": 5 }
  }
}
```

`severidad` values: `INFO | WARNING | ALERT | CRITICAL`

`tipo` values: `BEACON_FLOOD | DEAUTH | EVIL_TWIN | CADENA_OFENSIVA`

**Session reset** (broadcast after `POST /session/reset`):
```json
{
  "tipo": "session_reset"
}
```

**Detector status change:**
```json
{
  "tipo": "detector_status",
  "estado": "corriendo | detenido | error",
  "mensaje": "..."
}
```

### Frontend → Backend messages

```json
{ "comando": "status" }
```

```json
{ "comando": "ping" }
```

## Start the server

```bash
uvicorn warden.detector.web.server:app --host 127.0.0.1 --port 8000
# or override port:
python3 -m warden.defender.web --port 9000
```
