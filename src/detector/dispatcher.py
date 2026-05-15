"""Route a parsed Scapy packet to analyzer callbacks."""
from __future__ import annotations

from typing import Callable

from scapy.layers.dot11 import Dot11, Dot11Beacon

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
        if not pkt.haslayer(Dot11):  # type: ignore[attr-defined]
            return
        d11 = pkt[Dot11]  # type: ignore[index]
        if d11.type == 0 and d11.subtype == 8:  # management / beacon
            self._on_beacon(pkt)
            self._on_evil_twin(pkt)
        elif d11.type == 0 and d11.subtype == 12:  # management / deauth
            self._on_deauth(pkt)
