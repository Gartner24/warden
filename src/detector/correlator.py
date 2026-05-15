"""D-07: correlate three-phase attack alerts into CADENA_OFENSIVA."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from detector.config import DetectorConfig

__all__ = ["ChainCorrelator"]

_SEQUENCE = ("BEACON_FLOOD", "DEAUTH", "EVIL_TWIN")


class ChainCorrelator:
    def __init__(self, config: DetectorConfig) -> None:
        self._window = timedelta(seconds=config.ventana_correlacion_seg)
        self._timestamps: dict[str, datetime] = {}
        self._last_emitted_ts: datetime | None = None
        self._pending: list[dict[str, Any]] = []

    def consume(self, alert: dict[str, Any]) -> None:
        tipo = alert.get("tipo", "")
        if tipo not in _SEQUENCE:
            return
        ts = datetime.fromisoformat(alert["timestamp"])
        if self._last_emitted_ts is not None:
            if (ts - self._last_emitted_ts) < self._window:
                return
            self._timestamps.clear()
            self._last_emitted_ts = None
        self._timestamps[tipo] = ts
        if all(t in self._timestamps for t in _SEQUENCE):
            t0 = self._timestamps["BEACON_FLOOD"]
            t1 = self._timestamps["DEAUTH"]
            t2 = self._timestamps["EVIL_TWIN"]
            if t0 < t1 < t2 and (t2 - t0) <= self._window:
                self._last_emitted_ts = t2
                self._timestamps.clear()
                self._pending.append({
                    "timestamp": t2.isoformat(),
                    "severidad": "CRITICAL",
                    "tipo": "CADENA_OFENSIVA",
                    "mensaje": (
                        "Cadena ofensiva completa detectada"
                        " (Beacon Flood -> Deauth -> Evil Twin)"
                    ),
                    "detalles": {
                        "t_beacon_flood": t0.isoformat(),
                        "t_deauth": t1.isoformat(),
                        "t_evil_twin": t2.isoformat(),
                        "duracion_seg": (t2 - t0).total_seconds(),
                    },
                })

    def diag_snapshot(self) -> dict[str, Any]:
        return {
            "timestamps_seen": list(self._timestamps.keys()),
            "last_emitted_ts": self._last_emitted_ts.isoformat() if self._last_emitted_ts else None,
            "pending_count": len(self._pending),
        }

    def reset(self) -> None:
        self._timestamps.clear()
        self._last_emitted_ts = None
        self._pending.clear()

    def drain(self) -> list[dict[str, Any]]:
        out, self._pending = self._pending, []
        return out
