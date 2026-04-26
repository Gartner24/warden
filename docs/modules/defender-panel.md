# Module: Defender Panel

Source: `deliverables/warden-architecture.tex` lines 245-246, 527, 603-621, 1033-1083 (ADR-08)

Runtime: FastAPI 0.110+ / Uvicorn 0.27+ serving static HTML + vanilla JS + Tailwind CDN.

## Responsibilities

Real-time web dashboard for the detection operator. Served by the same FastAPI process that runs the detector. Receives alert events over an internal `asyncio.Queue` and pushes them to connected browsers via WebSocket.

## Endpoints

See [`../api/detector-fastapi.md`](../api/detector-fastapi.md) for the full contract.

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serves the Defender Panel HTML |
| `/ws` | WS | Streams detection events to the browser |
| `/api/status` | GET | Current session state (running, alerts) |
| `/api/session/reset` | POST | Clear all counters and restart |
| `/api/config` | GET / POST | Read or update detection thresholds at runtime |

## Source layout (planned)

```
src/detector/web/
|-- server.py            FastAPI app + lifespan (starts detector thread)
|-- websocket_manager.py Tracks active connections, broadcast helper
|-- routes.py            API route handlers
`-- static/
    |-- index.html
    |-- app.js
    `-- styles.css
```

## Start

```bash
uvicorn warden.detector.web.server:app --host 127.0.0.1 --port 8000
# or
python3 -m warden.defender.web
```

## Internal event flow

1. Detector analyzers push `{"type": "alert", "phase": "...", ...}` dicts to an `asyncio.Queue`.
2. `server.py` lifespan coroutine drains the queue and calls `websocket_manager.broadcast(event)`.
3. All connected Defender Panel browser tabs receive the event and update the UI without polling.
