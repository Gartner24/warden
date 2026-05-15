"""D-02: deauth flood detector keyed on protected BSSID."""
from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta
from typing import Any

from detector.config import DetectorConfig

__all__ = ["DeauthAnalyzer"]


class DeauthAnalyzer:
    def __init__(self, config: DetectorConfig) -> None:
        self._bssid_protegido = config.bssid_protegido.hex(":")
        self._window = timedelta(seconds=config.ventana_deauth_seg)
        self._threshold = config.umbral_deauth_por_seg
        self._cooldown = timedelta(seconds=config.cooldown_alerta_seg)
        self._buf: deque[tuple[datetime, str, str]] = deque()  # (ts, src, dst)
        self._pending: list[dict[str, Any]] = []
        self._last_alert: datetime | None = None
        self._observed_total = 0
        self._dropped_wrong_bssid = 0

    def observe(self, pkt: object, ts: datetime) -> None:
        from scapy.layers.dot11 import Dot11
        dot11 = pkt[Dot11]  # type: ignore[index]
        self._observed_total += 1
        addr2 = dot11.addr2
        addr3 = dot11.addr3
        if addr3 != self._bssid_protegido and addr2 != self._bssid_protegido:
            self._dropped_wrong_bssid += 1
            return
        src = dot11.addr2 or ""
        dst = dot11.addr1 or ""
        cutoff = ts - self._window
        while self._buf and self._buf[0][0] < cutoff:
            self._buf.popleft()
        self._buf.append((ts, src, dst))
        count = len(self._buf)
        rate = count / self._window.total_seconds()
        if rate >= self._threshold:
            if self._last_alert is None or (ts - self._last_alert) >= self._cooldown:
                src_unique = len({s for _, s, _ in self._buf})
                self._pending.append({
                    "timestamp": ts.isoformat(),
                    "severidad": "ALERT",
                    "tipo": "DEAUTH",
                    "mensaje": (
                        f"Deauth flood: {count} frames en"
                        f" {self._window.total_seconds():.0f}s"
                    ),
                    "detalles": {
                        "count": count,
                        "src_unique": src_unique,
                        "dst_unique": 1,
                        "tasa_por_seg": round(rate, 2),
                    },
                })
                self._last_alert = ts

    def diag_snapshot(self) -> dict[str, Any]:
        return {
            "observed_total": self._observed_total,
            "dropped_wrong_bssid": self._dropped_wrong_bssid,
            "pending_count": len(self._pending),
        }

    def drain(self) -> list[dict[str, Any]]:
        out, self._pending = self._pending, []
        return out
