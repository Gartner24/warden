"""D-01: anomalous unique-beacons-per-second detector with sliding window."""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Any

from detector.config import DetectorConfig

__all__ = ["BeaconFloodAnalyzer"]


class BeaconFloodAnalyzer:
    def __init__(self, config: DetectorConfig) -> None:
        self._window = timedelta(seconds=config.ventana_beacon_seg)
        self._threshold = config.umbral_beacons_por_seg
        self._cooldown = timedelta(seconds=config.cooldown_alerta_seg)
        self._buf: deque[tuple[datetime, bytes]] = deque()
        self._pending: list[dict[str, Any]] = []
        self._last_alert: datetime | None = None

    def observe(self, pkt: object, ts: datetime) -> None:
        from scapy.layers.dot11 import Dot11
        bssid_str = pkt[Dot11].addr2  # type: ignore[index]
        if bssid_str is None:
            return
        bssid = bytes.fromhex(bssid_str.replace(":", ""))
        cutoff = ts - self._window
        while self._buf and self._buf[0][0] < cutoff:
            self._buf.popleft()
        self._buf.append((ts, bssid))
        unique = len({b for _, b in self._buf})
        rate = unique / self._window.total_seconds()
        if rate < self._threshold:
            return
        # Suppress if within window+cooldown of last alert: the window covers
        # the period during which the original flood is "live", and cooldown
        # adds extra dead-time after that window expires.
        refractory = self._window + self._cooldown
        if self._last_alert is not None and (ts - self._last_alert) < refractory:
            return
        self._pending.append({
            "timestamp": ts.isoformat(),
            "severidad": "ALERT",
            "tipo": "BEACON_FLOOD",
            "mensaje": f"Beacon flood detectado: {rate:.1f} beacons/s (umbral {self._threshold})",
            "detalles": {
                "tasa_beacons_por_seg": round(rate, 2),
                "ventana_seg": self._window.total_seconds(),
                "bssids_unicos": unique,
            },
        })
        self._last_alert = ts

    def drain(self) -> list[dict[str, Any]]:
        out, self._pending = self._pending, []
        return out
