"""Passive scanner capture for network discovery.

Tries scapy.sniff() first (works when process has CAP_NET_RAW / runs as root).
Falls back to sudo -n tcpdump piped through PcapReader when scapy lacks
raw-socket permission — requires /etc/sudoers.d/warden to allow tcpdump.
Captures on whatever channel the interface is currently set to.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from typing import Callable

from scapy.all import sniff  # type: ignore[import-untyped]
from scapy.utils import PcapReader  # type: ignore[import-untyped]

__all__ = ["ScanCapture"]


class ScanCapture:
    def __init__(self, iface: str, on_packet: Callable[[object], None]) -> None:
        self.iface = iface
        self._on_packet = on_packet
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None
        self.last_error: str | None = None
        self.packets_seen: int = 0
        self.started_at: float | None = None

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

    def status(self) -> dict:
        return {
            "running": self.is_running(),
            "iface": self.iface,
            "packets_seen": self.packets_seen,
            "last_error": self.last_error,
        }

    def _wrap_packet(self, pkt: object) -> None:
        self.packets_seen += 1
        self._on_packet(pkt)

    def _run(self) -> None:
        self.started_at = time.monotonic()
        try:
            sniff(
                iface=self.iface,
                prn=self._wrap_packet,
                store=False,
                stop_filter=lambda _p: self._stop.is_set(),
            )
            return
        except PermissionError as exc:
            print(f"[ScanCapture] scapy needs privileges ({exc}), trying sudo tcpdump", file=sys.stderr)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            print(f"[ScanCapture] scapy failed: {self.last_error}", file=sys.stderr)
            return

        self._run_tcpdump()

    def _run_tcpdump(self) -> None:
        try:
            self._proc = subprocess.Popen(
                ["sudo", "-n", "tcpdump", "-i", self.iface, "-U", "-w", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(0.3)
            if self._proc.poll() is not None:
                err = (self._proc.stderr.read() or b"").decode(errors="replace").strip()
                self.last_error = f"tcpdump exited: {err[:200]}"
                print(f"[ScanCapture] {self.last_error}", file=sys.stderr)
                return
            with PcapReader(self._proc.stdout) as reader:
                for pkt in reader:
                    if self._stop.is_set():
                        break
                    self._wrap_packet(pkt)
        except Exception as exc:
            self.last_error = f"tcpdump failed: {type(exc).__name__}: {exc}"
            print(f"[ScanCapture] {self.last_error}", file=sys.stderr)
        finally:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
