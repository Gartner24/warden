"""Integration test: chain.pcap -> Defender Panel -> all 4 alert types observed."""
from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest

from detector.web.server import create_app

CHAIN_PCAP = str(Path("tests/fixtures/pcap/chain.pcap").resolve())


async def test_chain_pcap_triggers_all_alert_types():
    """Feed chain.pcap via /api/detector/start; verify 4 tipos reach broadcast."""
    app = create_app()
    broadcast_calls: list[dict] = []

    async with app.router.lifespan_context(app):
        original_broadcast = app.state.manager.broadcast

        async def _spy(msg: dict) -> None:
            broadcast_calls.append(msg)

        app.state.manager.broadcast = _spy  # type: ignore[assignment]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post(
                "/api/detector/start",
                json={
                    "bssid_protegido": "AA:BB:CC:DD:EE:FF",
                    "ssid_protegido": "LAB_WARDEN_UTP",
                    "pcap": CHAIN_PCAP,
                },
            )
            assert r.status_code == 200, r.text

        # Wait for detector thread to finish processing chain.pcap
        deadline = asyncio.get_event_loop().time() + 5.0
        while (
            app.state.runner.state == "corriendo"
            and asyncio.get_event_loop().time() < deadline
        ):
            await asyncio.sleep(0.1)

        # Give the drain task one extra cycle to flush the queue
        await asyncio.sleep(0.6)

    tipos = {m.get("tipo") for m in broadcast_calls}
    assert "BEACON_FLOOD" in tipos, f"got: {tipos}"
    assert "DEAUTH" in tipos, f"got: {tipos}"
    assert "EVIL_TWIN" in tipos, f"got: {tipos}"
    assert "CADENA_OFENSIVA" in tipos, f"got: {tipos}"
