"""Tests for WebSocketManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from detector.web.websocket_manager import WebSocketManager


def _make_ws(send_raises: bool = False) -> AsyncMock:
    ws = AsyncMock()
    if send_raises:
        from fastapi import WebSocketDisconnect
        ws.send_json.side_effect = WebSocketDisconnect()
    return ws


async def test_connect_adds_client():
    mgr = WebSocketManager()
    ws = _make_ws()
    await mgr.connect(ws)
    assert mgr.count == 1


async def test_disconnect_removes_client():
    mgr = WebSocketManager()
    ws = _make_ws()
    await mgr.connect(ws)
    mgr.disconnect(ws)
    assert mgr.count == 0


async def test_broadcast_sends_to_all():
    mgr = WebSocketManager()
    ws1 = _make_ws()
    ws2 = _make_ws()
    await mgr.connect(ws1)
    await mgr.connect(ws2)
    await mgr.broadcast({"tipo": "BEACON_FLOOD"})
    ws1.send_json.assert_called_once_with({"tipo": "BEACON_FLOOD"})
    ws2.send_json.assert_called_once_with({"tipo": "BEACON_FLOOD"})


async def test_broadcast_auto_removes_disconnected():
    mgr = WebSocketManager()
    ws_ok = _make_ws()
    ws_dead = _make_ws(send_raises=True)
    await mgr.connect(ws_ok)
    await mgr.connect(ws_dead)
    await mgr.broadcast({"tipo": "DEAUTH"})
    assert mgr.count == 1
    ws_ok.send_json.assert_called_once()
