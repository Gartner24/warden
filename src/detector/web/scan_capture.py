"""Passive scanner capture — thin wrapper around tcpdump for network discovery."""
from __future__ import annotations

import subprocess
import threading
from typing import Callable

from scapy.utils import PcapReader  # type: ignore[import-untyped]

__all__ = ["ScanCapture"]


class ScanCapture:
    def __init__(self, iface: str, on_packet: Callable[[object], None]) -> None:
        self.iface = iface
        self._on_packet = on_packet
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="warden-scan")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        self._proc = subprocess.Popen(
            ["sudo", "-n", "tcpdump", "-i", self.iface, "-U", "-w", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            with PcapReader(self._proc.stdout) as reader:
                for pkt in reader:
                    if self._stop.is_set():
                        break
                    self._on_packet(pkt)
        except Exception:
            pass
        finally:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
