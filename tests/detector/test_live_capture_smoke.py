from detector.capture.live_capture import LiveCapture
from detector.config import DetectorConfig


def test_live_capture_constructs():
    cfg = DetectorConfig(
        iface="lo", pcap_file=None, canal=6,
        bssid_protegido=bytes.fromhex("AABBCCDDEEFF"), ssid_protegido="X",
    )
    lc = LiveCapture(cfg, on_packet=lambda p: None)
    assert lc.iface == "lo"
    assert not lc.is_running()
