"""Route a parsed Scapy packet to analyzer callbacks."""
from __future__ import annotations

from typing import Callable

from scapy.layers.dot11 import Dot11Beacon, Dot11Deauth

__all__ = ["Dispatcher"]


class Dispatcher:
    def __init__(
        self,
        on_beacon: Callable[[object], None],
        on_evil_twin: Callable[[object], None],
        on_deauth: Callable[[object], None],
    ) -> None:
        self._on_beacon = on_beacon
        self._on_evil_twin = on_evil_twin
        self._on_deauth = on_deauth

    def dispatch(self, pkt: object) -> None:
        if pkt.haslayer(Dot11Beacon):  # type: ignore[attr-defined]
            self._on_beacon(pkt)
            self._on_evil_twin(pkt)
        elif pkt.haslayer(Dot11Deauth):  # type: ignore[attr-defined]
            self._on_deauth(pkt)
