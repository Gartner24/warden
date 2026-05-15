"""Passive scanner capture for network discovery.

Tries scapy.sniff() first (works when process has CAP_NET_RAW / runs as root).
Falls back to sudo -n tcpdump piped through PcapReader when scapy lacks
raw-socket permission — requires /etc/sudoers.d/warden to allow tcpdump.
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

_HOP_SEQUENCE = (1, 6, 11, 2, 7, 3, 8, 4, 9, 5, 10, 12, 13)


class ScanCapture:
    def __init__(self, iface: str, on_packet: Callable[[object], None]) -> None:
        self.iface = iface
        self._on_packet = on_packet
        self._thread: threading.Thread | None = None
        self._hop_thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._proc: subprocess.Popen | None = None
        self.last_error: str | None = None
        self.hop_error: str | None = None
        self.packets_seen: int = 0
        self.current_channel: int | None = None
        self.started_at: float | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="warden-scan")
        self._hop_thread = threading.Thread(target=self._hop_loop, daemon=True, name="warden-scan-hop")
        self._thread.start()
        self._hop_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        if self._thread:
            self._thread.join(timeout=2)
        if self._hop_thread:
            self._hop_thread.join(timeout=2)

    def status(self) -> dict:
        return {
            "running": self.is_running(),
            "iface": self.iface,
            "packets_seen": self.packets_seen,
            "current_channel": self.current_channel,
            "last_error": self.last_error,
            "hop_error": self.hop_error,
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
            return  # clean stop via stop_filter
        except PermissionError as exc:
            print(f"[ScanCapture] scapy needs privileges ({exc}), trying sudo tcpdump", file=sys.stderr)
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            print(f"[ScanCapture] scapy failed: {self.last_error}", file=sys.stderr)
            return

        # Fallback: sudo tcpdump -> PcapReader
        self._run_tcpdump()

    def _run_tcpdump(self) -> None:
        try:
            self._proc = subprocess.Popen(
                ["sudo", "-n", "tcpdump", "-i", self.iface, "-U", "-w", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Give tcpdump a moment to start, then check if it died immediately
            time.sleep(0.3)
            if self._proc.poll() is not None:
                err = (self._proc.stderr.read() or b"").decode(errors="replace").strip()
                self.last_error = f"tcpdump exited early: {err[:200]}"
                print(f"[ScanCapture] {self.last_error}", file=sys.stderr)
                return
            with PcapReader(self._proc.stdout) as reader:
                for pkt in reader:
                    if self._stop.is_set():
                        break
                    self._wrap_packet(pkt)
        except Exception as exc:
            self.last_error = f"tcpdump fallback failed: {type(exc).__name__}: {exc}"
            print(f"[ScanCapture] {self.last_error}", file=sys.stderr)
        finally:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._proc.kill()

    def _hop_loop(self) -> None:
        i = 0
        while not self._stop.is_set():
            ch = _HOP_SEQUENCE[i % len(_HOP_SEQUENCE)]
            try:
                r = subprocess.run(
                    ["sudo", "-n", "iw", "dev", self.iface, "set", "channel", str(ch)],
                    capture_output=True, text=True, timeout=2,
                )
                if r.returncode != 0:
                    self.hop_error = (r.stderr or r.stdout).strip()[:200]
                    return
                self.current_channel = ch
            except Exception as exc:
                self.hop_error = f"{type(exc).__name__}: {exc}"
                return
            i += 1
            for _ in range(3):
                if self._stop.is_set():
                    return
                time.sleep(0.1)
