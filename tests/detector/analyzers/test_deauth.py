from datetime import datetime, timedelta
from scapy.all import Dot11, Dot11Deauth

from detector.analyzers.deauth import DeauthAnalyzer
from detector.config import DetectorConfig

# "aa:bb:cc:dd:ee:ff" == bytes.fromhex("AABBCCDDEEFF")
PROTECTED_BSSID = bytes.fromhex("AABBCCDDEEFF")
PROTECTED_BSSID_STR = "aa:bb:cc:dd:ee:ff"


def _cfg(threshold=5, window=3):
    return DetectorConfig(
        iface="x", pcap_file=None, canal=6,
        bssid_protegido=PROTECTED_BSSID, ssid_protegido="LAB",
        umbral_deauth_por_seg=threshold, ventana_deauth_seg=window,
    )


def _deauth(src_idx: int):
    src = f"ee:ee:ee:ee:ee:{src_idx:02x}"
    return Dot11(addr1=PROTECTED_BSSID_STR,
                 addr2=src,
                 addr3=PROTECTED_BSSID_STR) / Dot11Deauth(reason=7)


def _deauth_other_bssid(src_idx: int):
    src = f"ee:ee:ee:ee:ee:{src_idx:02x}"
    return Dot11(addr1="ff:ff:ff:ff:ff:ff",
                 addr2=src,
                 addr3="00:00:00:00:00:01") / Dot11Deauth(reason=7)


def test_below_threshold_no_alert():
    a = DeauthAnalyzer(_cfg(threshold=5, window=3))
    base = datetime(2026, 1, 1, 12, 0, 0)
    # 10 deauths over 3s = ~3.3/s, below threshold of 5/s
    for i in range(10):
        a.observe(_deauth(i), base + timedelta(seconds=i * 0.3))
    assert a.drain() == []


def test_non_protected_bssid_ignored():
    a = DeauthAnalyzer(_cfg(threshold=1, window=3))
    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(50):
        a.observe(_deauth_other_bssid(i), base + timedelta(seconds=i * 0.01))
    assert a.drain() == []


def test_above_threshold_emits_alert():
    a = DeauthAnalyzer(_cfg(threshold=5, window=3))
    base = datetime(2026, 1, 1, 12, 0, 0)
    # 30 deauths in 3s = 10/s, above threshold of 5/s
    for i in range(30):
        a.observe(_deauth(i % 10), base + timedelta(seconds=i * 0.1))
    alerts = a.drain()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["tipo"] == "DEAUTH"
    assert alert["severidad"] == "ALERT"
    assert alert["detalles"]["count"] >= 15
    assert alert["detalles"]["src_unique"] >= 1
    assert alert["detalles"]["dst_unique"] == 1
    assert alert["detalles"]["tasa_por_seg"] >= 5


def test_cooldown_suppresses_repeat():
    a = DeauthAnalyzer(_cfg(threshold=5, window=3))
    base = datetime(2026, 1, 1, 12, 0, 0)
    # First burst -> alert
    for i in range(30):
        a.observe(_deauth(i % 10), base + timedelta(seconds=i * 0.1))
    # Second burst 2s later (within 5s cooldown)
    for i in range(30, 60):
        a.observe(_deauth(i % 10), base + timedelta(seconds=3 + (i - 30) * 0.1))
    assert len(a.drain()) == 1
