"""Live monitor-mode capture from a Scapy sniff() thread.

Hardware required at runtime; constructor + lifecycle are testable without it.
"""
from __future__ import annotations

import threading
from typing import Callable

from scapy.all import sniff  # type: ignore[import-untyped]

from detector.config import DetectorConfig

__all__ = ["LiveCapture"]


class LiveCapture:
    def __init__(self, config: DetectorConfig, on_packet: Callable[[object], None]) -> None:
        self.iface = config.iface
        self._on_packet = on_packet
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="warden-sniff")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        sniff(
            iface=self.iface,
            prn=self._on_packet,
            store=False,
            stop_filter=lambda _p: self._stop.is_set(),
        )
