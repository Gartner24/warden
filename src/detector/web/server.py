"""FastAPI application for the Defender Panel."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from detector.web.detector_runner import DetectorRunner
from detector.web.routes import router
from detector.web.websocket_manager import WebSocketManager

__all__ = ["create_app"]

_STATIC = Path(__file__).parent / "static"


async def _drain_queue(queue: asyncio.Queue[dict[str, Any]], manager: WebSocketManager) -> None:
    while True:
        try:
            alert = await asyncio.wait_for(queue.get(), timeout=0.5)
            await manager.broadcast(alert)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=2048)
    runner = DetectorRunner(queue=queue)
    manager = WebSocketManager()
    app.state.runner = runner
    app.state.manager = manager
    app.state.queue = queue
    app.state.seen_networks = None
    app.state.scanner = None
    drain_task = asyncio.create_task(_drain_queue(queue, manager))
    try:
        yield
    finally:
        drain_task.cancel()
        try:
            await drain_task
        except asyncio.CancelledError:
            pass
        runner.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="WARDEN Defender Panel", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket) -> None:
        manager: WebSocketManager = ws.app.state.manager
        await manager.connect(ws)
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("tipo") == "ping":
                    await ws.send_json({"tipo": "pong"})
        except WebSocketDisconnect:
            manager.disconnect(ws)

    if _STATIC.exists():
        app.mount("/", StaticFiles(directory=str(_STATIC), html=True), name="static")

    return app


app = create_app()
