"""Session-level counters wrapping the Reporter."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from detector.reporter import Reporter

__all__ = ["Session"]


class Session:
    def __init__(self, reporter: Reporter) -> None:
        self._reporter = reporter
        self._frames = 0
        self._start = datetime.now(timezone.utc)

    @property
    def frames_procesados(self) -> int:
        return self._frames

    @property
    def iniciado_en(self) -> datetime:
        return self._start

    @property
    def duracion_seg(self) -> float:
        return (datetime.now(timezone.utc) - self._start).total_seconds()

    def tick(self) -> None:
        self._frames += 1

    def summary(self) -> dict[str, Any]:
        return {
            "frames_procesados": self._frames,
            "duracion_seg": round(self.duracion_seg, 2),
            **self._reporter.summary(),
        }

    def reset(self) -> None:
        self._frames = 0
        self._start = datetime.now(timezone.utc)
        self._reporter._counters.clear()
        self._reporter._drops = 0
