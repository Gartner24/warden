# ADR-0008: FastAPI + WebSockets for the Defender Panel

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:1033`

## Context

The Defender Panel needs to display detection alerts as close to real time as possible. Polling the REST API introduces latency and wastes CPU on the defender laptop.

## Decision

Use FastAPI with a WebSocket endpoint (`/ws`). The detector pushes events to an `asyncio.Queue`; the FastAPI lifespan coroutine drains the queue and broadcasts to all connected browser tabs.

## Consequences

- Sub-second alert delivery to the browser without polling.
- The detector and the web server share a process; the queue is the only coupling point between the frame-capture thread and the async web server.
- Multiple browser tabs can watch the same session simultaneously via the WebSocket broadcast.
- If the WebSocket connection drops, the browser must reconnect; events during the gap are lost (acceptable for the live lab use case).
