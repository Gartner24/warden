"""Console + asyncio.Queue alert sink."""
from __future__ import annotations

import asyncio
import logging
import sys
from collections import Counter
from typing import Any

__all__ = ["Reporter", "format_console"]

_LOG = logging.getLogger(__name__)
_QUEUE_MAX = 2048
_DROP_LOG_EVERY = 1000


def format_console(alert: dict[str, Any]) -> str:
    return f"[{alert['timestamp']}] [{alert['severidad']}] {alert['tipo']}: {alert['mensaje']}"


class Reporter:
    def __init__(self, *, queue: asyncio.Queue | None = None) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = queue or asyncio.Queue(maxsize=_QUEUE_MAX)
        self._counters: Counter[str] = Counter()
        self._drops = 0

    @property
    def queue(self) -> asyncio.Queue[dict[str, Any]]:
        return self._queue

    def emit(self, alert: dict[str, Any]) -> None:
        print(format_console(alert), file=sys.stdout, flush=True)
        self._counters[alert["tipo"]] += 1
        try:
            self._queue.put_nowait(alert)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            self._queue.put_nowait(alert)
            self._drops += 1
            if self._drops % _DROP_LOG_EVERY == 0:
                _LOG.warning("reporter dropped %d alerts due to queue saturation", self._drops)

    def summary(self) -> dict[str, Any]:
        return {
            "alertas_totales": sum(self._counters.values()),
            "alertas_por_tipo": dict(self._counters),
            "alertas_descartadas": self._drops,
        }
