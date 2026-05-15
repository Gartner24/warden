"""Thread-based detector orchestrator feeding alerts into an asyncio.Queue."""
from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Any

_LOG = logging.getLogger(__name__)

from detector.analyzers.beacon_flood import BeaconFloodAnalyzer
from detector.analyzers.deauth import DeauthAnalyzer
from detector.analyzers.evil_twin import EvilTwinAnalyzer
from detector.capture.pcap_capture import iter_packets
from detector.config import DetectorConfig
from detector.correlator import ChainCorrelator
from detector.dispatcher import Dispatcher
from detector.reporter import Reporter
from detector.session import Session

__all__ = ["DetectorRunner", "RunnerStateError"]


class RunnerStateError(RuntimeError):
    """Raised when start() is called while already running."""


def _pkt_ts(pkt: Any) -> datetime:
    try:
        return datetime.fromtimestamp(float(pkt.time), tz=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


class DetectorRunner:
    def __init__(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._queue = queue
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._state = "detenido"
        self._lock = threading.Lock()
        self._correlator: Any = None
        self._evil_twin: Any = None

    @property
    def state(self) -> str:
        return self._state

    def start(self, config: DetectorConfig) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RunnerStateError("runner already running; call stop() first")
            self._stop_event.clear()
            self._state = "corriendo"
            self._thread = threading.Thread(
                target=self._run, args=(config,), daemon=True, name="warden-runner"
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._state = "detenido"

    def reset_correlator(self) -> None:
        if self._correlator is not None:
            self._correlator.reset()
        if self._evil_twin is not None:
            self._evil_twin.reset()

    def _run(self, config: DetectorConfig) -> None:
        try:
            reporter = Reporter(queue=self._queue)
            bf = BeaconFloodAnalyzer(config)
            da = DeauthAnalyzer(config)
            et = EvilTwinAnalyzer(config)
            cc = ChainCorrelator(config)
            self._correlator = cc
            self._evil_twin = et
            session = Session(reporter)
            _ts: list[datetime] = [datetime.now(timezone.utc)]
            dispatcher = Dispatcher(
                on_beacon=lambda p: bf.observe(p, _ts[0]),
                on_evil_twin=lambda p: et.observe(p, _ts[0]),
                on_deauth=lambda p: da.observe(p, _ts[0]),
            )
            if config.pcap_file:
                for pkt in iter_packets(config.pcap_file):
                    if self._stop_event.is_set():
                        break
                    _ts[0] = _pkt_ts(pkt)
                    dispatcher.dispatch(pkt)
                    for alert in bf.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in da.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in et.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in cc.drain():
                        reporter.emit(alert)
                    session.tick()
            else:
                from detector.capture.live_capture import LiveCapture

                def _on_packet(pkt: Any) -> None:
                    _ts[0] = _pkt_ts(pkt)
                    dispatcher.dispatch(pkt)
                    for alert in bf.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in da.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in et.drain():
                        reporter.emit(alert)
                        cc.consume(alert)
                    for alert in cc.drain():
                        reporter.emit(alert)
                    session.tick()

                cap = LiveCapture(config=config, on_packet=_on_packet)
                cap.start()
                while not self._stop_event.is_set():
                    try:
                        self._queue.put_nowait({
                            "tipo": "diag",
                            "beacon_flood": bf.diag_snapshot(),
                            "deauth": da.diag_snapshot(),
                            "evil_twin": et.diag_snapshot(),
                            "correlator": cc.diag_snapshot(),
                        })
                    except Exception:
                        pass
                    self._stop_event.wait(timeout=1.0)
                cap.stop()
        except Exception as exc:
            _LOG.exception("detector thread crashed")
            self._state = "error"
            try:
                self._queue.put_nowait({"tipo": "error", "mensaje": str(exc)})
            except Exception:
                pass
        finally:
            self._correlator = None
            self._evil_twin = None
            if self._state != "error":
                self._state = "detenido"
