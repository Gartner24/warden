import asyncio
from datetime import datetime
from detector.reporter import Reporter
from detector.session import Session


def test_session_initial_state():
    r = Reporter()
    s = Session(r)
    assert s.frames_procesados == 0
    assert isinstance(s.iniciado_en, datetime)


def test_tick_increments_frames():
    r = Reporter()
    s = Session(r)
    s.tick()
    s.tick()
    assert s.frames_procesados == 2


def test_summary_includes_reporter_data():
    r = Reporter()
    r.emit({"tipo": "BEACON_FLOOD", "timestamp": "2026-01-01T00:00:00", "severidad": "ALERT", "mensaje": "x", "detalles": {}})
    s = Session(r)
    s.tick()
    summary = s.summary()
    assert summary["frames_procesados"] == 1
    assert summary["alertas_totales"] == 1


def test_reset_clears_counters():
    r = Reporter()
    s = Session(r)
    s.tick()
    s.tick()
    s.reset()
    assert s.frames_procesados == 0
