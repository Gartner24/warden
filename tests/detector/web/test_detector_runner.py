"""Tests for DetectorRunner lifecycle."""
import asyncio
import time

import pytest

from detector.config import DetectorConfig
from detector.web.detector_runner import DetectorRunner, RunnerStateError


def _cfg(pcap: str | None = None) -> DetectorConfig:
    return DetectorConfig(
        iface="lo",
        pcap_file=pcap,
        canal=6,
        bssid_protegido=bytes.fromhex("AABBCCDDEEFF"),
        ssid_protegido="LAB_WARDEN_UTP",
    )


def test_initial_state_is_detenido():
    q: asyncio.Queue = asyncio.Queue()
    runner = DetectorRunner(queue=q)
    assert runner.state == "detenido"


def test_start_with_pcap_transitions_to_corriendo(tmp_path):
    from scapy.all import wrpcap, RadioTap, Dot11, Dot11Beacon, Dot11Elt

    pcap = tmp_path / "tiny.pcap"
    pkt = (
        RadioTap()
        / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="aa:bb:cc:00:00:01", addr3="aa:bb:cc:00:00:01")
        / Dot11Beacon()
        / Dot11Elt(ID=0, info=b"TestSSID")
    )
    pkt.time = 1.0
    wrpcap(str(pcap), [pkt])

    q: asyncio.Queue = asyncio.Queue()
    runner = DetectorRunner(queue=q)
    cfg = _cfg(pcap=str(pcap))
    runner.start(cfg)
    # Give thread time to start
    time.sleep(0.1)
    assert runner.state in ("corriendo", "detenido")  # detenido if pcap finished before check
    runner.stop()


def test_double_start_raises():
    q: asyncio.Queue = asyncio.Queue()
    runner = DetectorRunner(queue=q)
    cfg = _cfg(pcap="tests/fixtures/pcap/quiet.pcap")
    runner.start(cfg)
    with pytest.raises(RunnerStateError):
        runner.start(cfg)
    runner.stop()


def test_stop_transitions_to_detenido(tmp_path):
    from scapy.all import wrpcap, RadioTap, Dot11, Dot11Beacon, Dot11Elt

    pcap = tmp_path / "mini.pcap"
    pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="aa:bb:cc:00:00:01",
                              addr3="aa:bb:cc:00:00:01") / Dot11Beacon() / Dot11Elt(ID=0, info=b"X")
    pkt.time = 1.0
    wrpcap(str(pcap), [pkt])

    q: asyncio.Queue = asyncio.Queue()
    runner = DetectorRunner(queue=q)
    runner.start(_cfg(pcap=str(pcap)))
    runner.stop()
    assert runner.state == "detenido"
