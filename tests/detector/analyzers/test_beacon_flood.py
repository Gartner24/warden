from datetime import datetime, timedelta
from scapy.all import RadioTap, Dot11, Dot11Beacon, Dot11Elt

from detector.analyzers.beacon_flood import BeaconFloodAnalyzer
from detector.config import DetectorConfig


def _cfg(threshold=30, window=5):
    return DetectorConfig(
        iface="x", pcap_file=None, canal=6,
        bssid_protegido=bytes.fromhex("AABBCCDDEEFF"), ssid_protegido="LAB",
        umbral_beacons_por_seg=threshold, ventana_beacon_seg=window,
    )


def _beacon(b: int):
    bssid = f"aa:bb:cc:00:00:{b:02x}"
    return Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid) \
        / Dot11Beacon() / Dot11Elt(ID=0, info=f"FakeNet_{b}".encode())


def test_below_threshold_no_alert():
    a = BeaconFloodAnalyzer(_cfg())
    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(50):  # 50 beacons over 5s = 10/s, below 30/s
        a.observe(_beacon(i), base + timedelta(seconds=i / 10))
    assert a.drain() == []


def test_above_threshold_emits_alert():
    a = BeaconFloodAnalyzer(_cfg(threshold=30, window=5))
    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(200):  # 200 unique BSSIDs in 5s = 40/s
        a.observe(_beacon(i), base + timedelta(seconds=(i / 40)))
    alerts = a.drain()
    assert len(alerts) == 1
    assert alerts[0]["tipo"] == "BEACON_FLOOD"
    assert alerts[0]["severidad"] == "ALERT"
    assert alerts[0]["detalles"]["tasa_beacons_por_seg"] >= 30


def test_cooldown_suppresses_repeat():
    a = BeaconFloodAnalyzer(_cfg(threshold=10, window=5))
    base = datetime(2026, 1, 1, 12, 0, 0)
    # First burst -> alert
    for i in range(100):
        a.observe(_beacon(i), base + timedelta(seconds=(i / 30)))
    # Second burst 2s later (within 5s cooldown) -> no new alert
    for i in range(100, 200):
        a.observe(_beacon(i), base + timedelta(seconds=4 + (i / 30)))
    assert len(a.drain()) == 1
