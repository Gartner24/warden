from datetime import datetime, timedelta
from detector.correlator import ChainCorrelator
from detector.config import DetectorConfig


def _cfg(window=60):
    return DetectorConfig(
        iface="x", pcap_file=None, canal=6,
        bssid_protegido=bytes.fromhex("AABBCCDDEEFF"), ssid_protegido="LAB",
        ventana_correlacion_seg=window,
    )


def _alert(tipo: str, ts: datetime) -> dict:
    return {"tipo": tipo, "timestamp": ts.isoformat(), "severidad": "ALERT", "mensaje": "", "detalles": {}}


def test_three_in_sequence_emits_chain():
    cc = ChainCorrelator(_cfg())
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("BEACON_FLOOD", base))
    cc.consume(_alert("DEAUTH", base + timedelta(seconds=15)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=35)))
    alerts = cc.drain()
    assert len(alerts) == 1
    assert alerts[0]["tipo"] == "CADENA_OFENSIVA"
    assert alerts[0]["severidad"] == "CRITICAL"


def test_out_of_order_no_chain():
    cc = ChainCorrelator(_cfg())
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("DEAUTH", base))
    cc.consume(_alert("BEACON_FLOOD", base + timedelta(seconds=5)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=10)))
    assert cc.drain() == []


def test_window_exceeded_no_chain():
    cc = ChainCorrelator(_cfg(window=30))
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("BEACON_FLOOD", base))
    cc.consume(_alert("DEAUTH", base + timedelta(seconds=15)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=35)))  # span=35 > window=30
    assert cc.drain() == []


def test_chain_emitted_only_once():
    cc = ChainCorrelator(_cfg())
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("BEACON_FLOOD", base))
    cc.consume(_alert("DEAUTH", base + timedelta(seconds=10)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=20)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=25)))  # extra evil twin
    assert len(cc.drain()) == 1


def test_chain_can_fire_again_after_reset():
    cc = ChainCorrelator(_cfg())
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("BEACON_FLOOD", base))
    cc.consume(_alert("DEAUTH", base + timedelta(seconds=10)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=20)))
    assert len(cc.drain()) == 1
    cc.reset()
    base2 = base + timedelta(seconds=120)
    cc.consume(_alert("BEACON_FLOOD", base2))
    cc.consume(_alert("DEAUTH", base2 + timedelta(seconds=10)))
    cc.consume(_alert("EVIL_TWIN", base2 + timedelta(seconds=20)))
    assert len(cc.drain()) == 1


def test_chain_fires_only_once_within_refractory():
    """Second chain within 60s of first is suppressed (refractory)."""
    cc = ChainCorrelator(_cfg(window=60))
    base = datetime(2026, 1, 1, 12, 0, 0)
    cc.consume(_alert("BEACON_FLOOD", base))
    cc.consume(_alert("DEAUTH", base + timedelta(seconds=10)))
    cc.consume(_alert("EVIL_TWIN", base + timedelta(seconds=20)))
    assert len(cc.drain()) == 1
    # Try again 30s later (within 60s refractory)
    base2 = base + timedelta(seconds=30)
    cc.consume(_alert("BEACON_FLOOD", base2))
    cc.consume(_alert("DEAUTH", base2 + timedelta(seconds=5)))
    cc.consume(_alert("EVIL_TWIN", base2 + timedelta(seconds=10)))
    assert len(cc.drain()) == 0  # still suppressed
