"""Detector CLI entry point. Wires capture -> dispatcher -> analyzers -> correlator -> reporter."""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from typing import Any

from detector.analyzers.beacon_flood import BeaconFloodAnalyzer
from detector.analyzers.deauth import DeauthAnalyzer
from detector.analyzers.evil_twin import EvilTwinAnalyzer
from detector.capture.pcap_capture import iter_packets
from detector.config import parse_args
from detector.correlator import ChainCorrelator
from detector.dispatcher import Dispatcher
from detector.reporter import Reporter
from detector.session import Session

__all__ = ["run_pcap_session", "run_live_session"]


def _pkt_ts(pkt: Any) -> datetime:
    try:
        return datetime.fromtimestamp(float(pkt.time), tz=timezone.utc)
    except (AttributeError, ValueError, OSError):
        return datetime.now(timezone.utc)


async def run_pcap_session(argv: list[str]) -> None:
    cfg = parse_args(argv)
    reporter = Reporter()
    bf = BeaconFloodAnalyzer(cfg)
    da = DeauthAnalyzer(cfg)
    et = EvilTwinAnalyzer(cfg)
    cc = ChainCorrelator(cfg)
    session = Session(reporter)

    _ts: list[datetime] = [datetime.now(timezone.utc)]

    dispatcher = Dispatcher(
        on_beacon=lambda p: bf.observe(p, _ts[0]),
        on_evil_twin=lambda p: et.observe(p, _ts[0]),
        on_deauth=lambda p: da.observe(p, _ts[0]),
    )

    assert cfg.pcap_file is not None
    for pkt in iter_packets(cfg.pcap_file):
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

    print(session.summary(), file=sys.stderr)


async def run_live_session(argv: list[str]) -> None:
    raise NotImplementedError("live session deferred to Phase 9 hardware day")


def main() -> int:
    asyncio.run(run_pcap_session(sys.argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
