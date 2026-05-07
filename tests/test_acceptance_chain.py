"""End-to-end acceptance test: chain.pcap -> Defender Panel -> all 4 alert tipos via WS."""
import asyncio
from pathlib import Path

import httpx
import pytest

from detector.web.server import create_app

CHAIN_PCAP = str(Path("tests/fixtures/pcap/chain.pcap").resolve())


async def test_acceptance_chain_triggers_all_alert_types():
    """Full pipeline: chain.pcap -> FastAPI server -> broadcast -> 4 tipos confirmed."""
    app = create_app()
    broadcast_calls: list[dict] = []

    async with app.router.lifespan_context(app):
        async def _spy(msg: dict) -> None:
            broadcast_calls.append(msg)

        app.state.manager.broadcast = _spy  # type: ignore[assignment]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/detector/start", json={
                "bssid_protegido": "AA:BB:CC:DD:EE:FF",
                "ssid_protegido": "LAB_WARDEN_UTP",
                "pcap": CHAIN_PCAP,
            })
            assert r.status_code == 200

        # Wait for chain.pcap to be fully processed and queue drained
        await asyncio.sleep(3.0)

    tipos = {m.get("tipo") for m in broadcast_calls}
    assert "BEACON_FLOOD" in tipos, f"got: {tipos}"
    assert "DEAUTH" in tipos, f"got: {tipos}"
    assert "EVIL_TWIN" in tipos, f"got: {tipos}"
    assert "CADENA_OFENSIVA" in tipos, f"got: {tipos}"


async def test_session_reset_broadcasts_reset_message():
    """POST /api/session/reset -> manager.broadcast called with tipo=session_reset."""
    app = create_app()
    broadcast_calls: list[dict] = []

    async with app.router.lifespan_context(app):
        async def _spy(msg: dict) -> None:
            broadcast_calls.append(msg)

        app.state.manager.broadcast = _spy  # type: ignore[assignment]

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/api/session/reset")
            assert r.status_code == 200

    assert any(m.get("tipo") == "session_reset" for m in broadcast_calls)


async def test_live_parity_dispatcher_matches_synthetic():
    """Radiotap-prefixed live-parity fixture dispatches same as synthetic frames."""
    from scapy.all import rdpcap
    from detector.dispatcher import Dispatcher

    pkts = list(rdpcap("tests/fixtures/pcap/live-parity-radiotap.pcap"))
    counts = {"beacon": 0, "evil_twin": 0, "deauth": 0}
    d = Dispatcher(
        on_beacon=lambda p: counts.__setitem__("beacon", counts["beacon"] + 1),
        on_evil_twin=lambda p: counts.__setitem__("evil_twin", counts["evil_twin"] + 1),
        on_deauth=lambda p: counts.__setitem__("deauth", counts["deauth"] + 1),
    )
    for p in pkts:
        d.dispatch(p)
    assert counts == {"beacon": 1, "evil_twin": 1, "deauth": 1}
