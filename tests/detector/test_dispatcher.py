import pytest
from scapy.all import RadioTap, Dot11, Dot11Beacon, Dot11Deauth, Dot11Elt

from detector.dispatcher import Dispatcher


def _beacon():
    return RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff",
                              addr2="aa:bb:cc:00:00:01",
                              addr3="aa:bb:cc:00:00:01") / Dot11Beacon() / Dot11Elt(ID=0, info=b"S")


def _deauth():
    return RadioTap() / Dot11(addr1="00:00:00:00:00:00",
                              addr2="aa:bb:cc:00:00:01",
                              addr3="aa:bb:cc:00:00:01") / Dot11Deauth(reason=7)


def test_beacon_routes_to_two_handlers():
    calls = {"beacon": 0, "evil_twin": 0, "deauth": 0}
    d = Dispatcher(
        on_beacon=lambda p: calls.__setitem__("beacon", calls["beacon"] + 1),
        on_evil_twin=lambda p: calls.__setitem__("evil_twin", calls["evil_twin"] + 1),
        on_deauth=lambda p: calls.__setitem__("deauth", calls["deauth"] + 1),
    )
    d.dispatch(_beacon())
    assert calls == {"beacon": 1, "evil_twin": 1, "deauth": 0}


def test_deauth_routes_to_deauth_handler():
    calls = {"beacon": 0, "evil_twin": 0, "deauth": 0}
    d = Dispatcher(
        on_beacon=lambda p: calls.__setitem__("beacon", calls["beacon"] + 1),
        on_evil_twin=lambda p: calls.__setitem__("evil_twin", calls["evil_twin"] + 1),
        on_deauth=lambda p: calls.__setitem__("deauth", calls["deauth"] + 1),
    )
    d.dispatch(_deauth())
    assert calls == {"beacon": 0, "evil_twin": 0, "deauth": 1}


def test_unknown_frame_ignored():
    calls = {"n": 0}
    d = Dispatcher(
        on_beacon=lambda p: calls.__setitem__("n", calls["n"] + 1),
        on_evil_twin=lambda p: calls.__setitem__("n", calls["n"] + 1),
        on_deauth=lambda p: calls.__setitem__("n", calls["n"] + 1),
    )
    d.dispatch(RadioTap() / Dot11(type=2))  # data frame
    assert calls == {"n": 0}


def test_works_without_radiotap():
    """Synthetic frames without RadioTap layer must still dispatch."""
    pkt = Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2="aa:bb:cc:00:00:01",
                addr3="aa:bb:cc:00:00:01") / Dot11Beacon() / Dot11Elt(ID=0, info=b"S")
    calls = {"n": 0}
    d = Dispatcher(
        on_beacon=lambda p: calls.__setitem__("n", calls["n"] + 1),
        on_evil_twin=lambda p: calls.__setitem__("n", calls["n"] + 1),
        on_deauth=lambda p: None,
    )
    d.dispatch(pkt)
    assert calls["n"] == 2
