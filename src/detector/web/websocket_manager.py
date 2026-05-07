"""Tracks connected WebSocket clients and broadcasts messages to all of them."""
from __future__ import annotations

from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

__all__ = ["WebSocketManager"]


class WebSocketManager:
    def __init__(self) -> None:
        self._clients: list[WebSocket] = []

    @property
    def count(self) -> int:
        return len(self._clients)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients = [c for c in self._clients if c is not ws]

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
