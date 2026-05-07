import pytest
from pathlib import Path
from scapy.all import wrpcap, RadioTap, Dot11, Dot11Beacon, Dot11Elt

from detector.capture.pcap_capture import iter_packets


@pytest.fixture
def tiny_beacon_pcap(tmp_path):
    pkts = [
        RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff",
                           addr2="aa:bb:cc:00:00:01",
                           addr3="aa:bb:cc:00:00:01") / Dot11Beacon() / Dot11Elt(ID=0, info=b"X"),
        RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff",
                           addr2="aa:bb:cc:00:00:02",
                           addr3="aa:bb:cc:00:00:02") / Dot11Beacon() / Dot11Elt(ID=0, info=b"Y"),
    ]
    p = tmp_path / "tiny.pcap"
    wrpcap(str(p), pkts)
    return p


def test_iter_packets_yields_dot11(tiny_beacon_pcap):
    pkts = list(iter_packets(tiny_beacon_pcap))
    assert len(pkts) == 2
    from scapy.layers.dot11 import Dot11Beacon
    assert all(p.haslayer(Dot11Beacon) for p in pkts)


def test_iter_packets_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(iter_packets(tmp_path / "nope.pcap"))
