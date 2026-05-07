import pytest
from detector.config import DetectorConfig, parse_args, ConfigError


def test_parse_args_defaults():
    cfg = parse_args(["--bssid", "AA:BB:CC:DD:EE:FF", "--ssid", "LAB_WARDEN_UTP"])
    assert cfg.iface == "panda0"
    assert cfg.canal == 6
    assert cfg.umbral_beacons_por_seg == 30
    assert cfg.ventana_beacon_seg == 5
    assert cfg.umbral_deauth_por_seg == 5
    assert cfg.ventana_deauth_seg == 3
    assert cfg.ventana_correlacion_seg == 60
    assert cfg.bssid_protegido == bytes.fromhex("AABBCCDDEEFF")
    assert cfg.ssid_protegido == "LAB_WARDEN_UTP"
    assert cfg.pcap_file is None


def test_pcap_and_iface_are_mutex():
    with pytest.raises(ConfigError):
        parse_args(["--bssid", "AA:BB:CC:DD:EE:FF", "--ssid", "X", "--iface", "eth0", "--pcap", "x.pcap"])


def test_invalid_bssid_rejected():
    with pytest.raises(ConfigError):
        parse_args(["--bssid", "GG:HH:II:JJ:KK:LL", "--ssid", "X"])


def test_channel_range_validated():
    with pytest.raises(ConfigError):
        parse_args(["--bssid", "AA:BB:CC:DD:EE:FF", "--ssid", "X", "--channel", "14"])
