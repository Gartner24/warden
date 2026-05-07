import asyncio
from detector.reporter import Reporter, format_console


def _alert(tipo: str = "BEACON_FLOOD") -> dict:
    return {
        "timestamp": "2026-01-01T12:00:00",
        "severidad": "ALERT",
        "tipo": tipo,
        "mensaje": "test",
        "detalles": {},
    }


def test_format_console_contains_severity_and_tipo():
    line = format_console(_alert())
    assert "ALERT" in line
    assert "BEACON_FLOOD" in line
    assert "2026-01-01" in line


def test_emit_pushes_to_queue():
    r = Reporter()
    r.emit(_alert())
    assert r.queue.qsize() == 1


def test_full_queue_drops_oldest():
    import asyncio
    q = asyncio.Queue(maxsize=3)
    # pre-fill
    for i in range(3):
        q.put_nowait({"tipo": f"OLD_{i}"})
    r = Reporter(queue=q)
    r.emit(_alert("NEW"))
    # queue still size 3, oldest dropped
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    tipos = [i["tipo"] for i in items]
    assert "OLD_0" not in tipos
    assert "NEW" in tipos


def test_summary_counts_by_tipo():
    r = Reporter()
    r.emit(_alert("BEACON_FLOOD"))
    r.emit(_alert("BEACON_FLOOD"))
    r.emit(_alert("DEAUTH"))
    s = r.summary()
    assert s["alertas_totales"] == 3
    assert s["alertas_por_tipo"]["BEACON_FLOOD"] == 2
    assert s["alertas_por_tipo"]["DEAUTH"] == 1
