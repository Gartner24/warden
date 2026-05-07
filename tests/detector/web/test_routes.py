"""Tests for Defender Panel API routes."""
import asyncio
from unittest.mock import MagicMock, AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from detector.web.routes import router
from detector.web.detector_runner import DetectorRunner
from detector.web.websocket_manager import WebSocketManager


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    q: asyncio.Queue = asyncio.Queue()
    runner = MagicMock(spec=DetectorRunner)
    runner.state = "detenido"
    runner.start = MagicMock()
    runner.stop = MagicMock()
    mgr = MagicMock(spec=WebSocketManager)
    mgr.broadcast = AsyncMock()
    mgr.count = 0
    app.state.runner = runner
    app.state.manager = mgr
    app.state.queue = q
    return app


async def test_get_status_shape():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert "detector_corriendo" in body
    assert "alertas_totales" in body
    assert "frames_procesados" in body


async def test_detector_start_returns_ok():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/detector/start", json={
            "bssid_protegido": "AA:BB:CC:DD:EE:FF",
            "ssid_protegido": "LAB",
            "iface": "lo",
        })
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_detector_stop_returns_ok():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/detector/stop")
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_session_reset_broadcasts():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/session/reset")
    assert r.status_code == 200
    app.state.manager.broadcast.assert_called_once()
    msg = app.state.manager.broadcast.call_args[0][0]
    assert msg.get("tipo") == "session_reset"


async def test_get_config_returns_thresholds():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/config")
    assert r.status_code == 200
    body = r.json()
    assert "umbrales" in body


async def test_post_config_updates_thresholds():
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/api/config", json={"umbrales": {"umbral_beacons_por_seg": 25}})
    assert r.status_code == 200
    assert r.json()["ok"] is True
