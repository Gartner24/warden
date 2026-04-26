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

## WebSocket

`ws://127.0.0.1:8000/ws`

The server pushes JSON events to all connected clients. The browser does not send messages over this socket.

### Event schema (TBD - to be finalized during implementation)

```json
{
  "type": "alert",
  "phase": "beacon_flood | deauth | evil_twin | chain",
  "detection_id": "D-01 | D-02 | D-03 | D-07",
  "timestamp": "<ISO-8601>",
  "details": {}
}
```

```json
{
  "type": "status",
  "state": "running | stopped",
  "timestamp": "<ISO-8601>"
}
```

## Start the server

```bash
uvicorn warden.detector.web.server:app --host 127.0.0.1 --port 8000
# or override port:
python3 -m warden.defender.web --port 9000
```
