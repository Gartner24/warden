from scapy.all import rdpcap

from detector.dispatcher import Dispatcher


def test_radiotap_fixture_dispatches_both_layers():
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
