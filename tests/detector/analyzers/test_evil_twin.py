from datetime import datetime
from scapy.all import Dot11, Dot11Beacon, Dot11Elt

from detector.analyzers.evil_twin import EvilTwinAnalyzer
from detector.config import DetectorConfig

PROTECTED_BSSID = bytes.fromhex("AABBCCDDEEFF")
PROTECTED_BSSID_STR = "aa:bb:cc:dd:ee:ff"
SSID = "LAB_WARDEN_UTP"
ROGUE_BSSID_STR = "00:11:22:33:44:55"
ROGUE_BSSID = bytes.fromhex("001122334455")
TS = datetime(2026, 1, 1, 12, 0, 0)


def _cfg(whitelist=()):
    return DetectorConfig(
        iface="x", pcap_file=None, canal=6,
        bssid_protegido=PROTECTED_BSSID, ssid_protegido=SSID,
        bssid_lista_blanca=tuple(whitelist),
    )


def _beacon(bssid: str, ssid: str):
    return Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=bssid, addr3=bssid) \
        / Dot11Beacon() / Dot11Elt(ID=0, info=ssid.encode())


def test_legit_bssid_no_alert():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(PROTECTED_BSSID_STR, SSID), TS)
    assert a.drain() == []


def test_different_ssid_no_alert():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, "SOME_OTHER_SSID"), TS)
    assert a.drain() == []


def test_rogue_bssid_emits_critical_alert():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    alerts = a.drain()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["tipo"] == "EVIL_TWIN"
    assert alert["severidad"] == "CRITICAL"
    assert alert["detalles"]["ssid"] == SSID
    assert alert["detalles"]["bssid_legitimo"] == PROTECTED_BSSID_STR
    assert alert["detalles"]["bssid_clon"] == ROGUE_BSSID_STR


def test_whitelist_suppresses_alert():
    a = EvilTwinAnalyzer(_cfg(whitelist=(ROGUE_BSSID,)))
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    assert a.drain() == []


def test_dedup_same_rogue_bssid():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    assert len(a.drain()) == 1


def test_ssid_trailing_space_still_matches():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, SSID + " "), TS)
    assert len(a.drain()) == 1


def test_ssid_different_case_still_matches():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, SSID.lower()), TS)
    assert len(a.drain()) == 1


def test_reset_allows_re_detection():
    a = EvilTwinAnalyzer(_cfg())
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    a.drain()
    a.reset()
    a.observe(_beacon(ROGUE_BSSID_STR, SSID), TS)
    assert len(a.drain()) == 1
