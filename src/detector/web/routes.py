"""Defender Panel REST API routes."""
from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from detector.config import ConfigError, DetectorConfig
from detector.web.detector_runner import RunnerStateError

_SCRIPTS_DIR = Path(__file__).parents[3] / "scripts"
_MONITOR_SCRIPT = _SCRIPTS_DIR / "setup-monitor-mode.sh"

__all__ = ["router"]

router = APIRouter()

# Per-process config state for threshold overrides
_current_config: dict[str, Any] = {
    "umbrales": {
        "umbral_beacons_por_seg": 30,
        "ventana_beacon_seg": 5,
        "umbral_deauth_por_seg": 5,
        "ventana_deauth_seg": 3,
        "cooldown_alerta_seg": 5,
    }
}


def _runner(request: Request) -> Any:
    return request.app.state.runner


def _manager(request: Request) -> Any:
    return request.app.state.manager


@router.get("/api/status")
async def get_status(request: Request) -> dict[str, Any]:
    runner = _runner(request)
    return {
        "detector_corriendo": runner.state == "corriendo",
        "estado": runner.state,
        "duracion_seg": 0,
        "frames_procesados": 0,
        "alertas_totales": 0,
        "alertas_recientes": [],
        "alertas_por_tipo": {
            "BEACON_FLOOD": 0,
            "DEAUTH": 0,
            "EVIL_TWIN": 0,
            "CADENA_OFENSIVA": 0,
        },
    }


@router.post("/api/session/reset")
async def session_reset(request: Request) -> dict[str, Any]:
    manager = _manager(request)
    runner = _runner(request)
    runner.reset_correlator()
    await manager.broadcast({"tipo": "session_reset"})
    return {"ok": True, "mensaje": "Sesion reiniciada."}


@router.get("/api/config")
async def get_config() -> dict[str, Any]:
    return _current_config


@router.post("/api/config")
async def post_config(request: Request) -> dict[str, Any]:
    body = await request.json()
    if "umbrales" in body:
        _current_config["umbrales"].update(body["umbrales"])
    return {"ok": True, "config": _current_config}


@router.post("/api/detector/start")
async def detector_start(request: Request) -> JSONResponse:
    body = await request.json()
    runner = _runner(request)
    bssid = body.get("bssid_protegido", "")
    ssid = body.get("ssid_protegido", "")
    iface = body.get("iface", "panda0")
    pcap = body.get("pcap")
    canal = body.get("canal", 6)
    try:
        cfg = DetectorConfig(
            iface=iface,
            pcap_file=pcap,
            canal=canal,
            bssid_protegido=bytes.fromhex(bssid.replace(":", "")),
            ssid_protegido=ssid,
            **{k: v for k, v in _current_config["umbrales"].items()},
        )
        runner.start(cfg)
    except RunnerStateError as exc:
        return JSONResponse(
            {"ok": False, "error": str(exc), "codigo": "DETECTOR_ALREADY_RUNNING"},
            status_code=409,
        )
    except (ConfigError, ValueError) as exc:
        return JSONResponse(
            {"ok": False, "error": str(exc), "codigo": "INVALID_CONFIG"},
            status_code=400,
        )
    await _manager(request).broadcast({"tipo": "detector_status", "estado": "corriendo"})
    return JSONResponse({"ok": True, "mensaje": f"Detector iniciado en {iface} canal {canal}."})


@router.post("/api/detector/stop")
async def detector_stop(request: Request) -> dict[str, Any]:
    runner = _runner(request)
    runner.stop()
    await _manager(request).broadcast({"tipo": "detector_status", "estado": "detenido"})
    return {"ok": True, "mensaje": "Detector detenido."}


@router.get("/api/interface/status")
async def interface_status() -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["iw", "dev", "panda0", "info"],
            capture_output=True, text=True, timeout=3,
        )
        mode = "unknown"
        channel: int | None = None
        for line in result.stdout.splitlines():
            s = line.strip()
            if s.startswith("type "):
                mode = s.split(None, 1)[1]
            elif s.startswith("channel "):
                try:
                    channel = int(s.split()[1])
                except (IndexError, ValueError):
                    pass
        return {"ok": True, "iface": "panda0", "mode": mode, "channel": channel}
    except FileNotFoundError:
        return {"ok": False, "iface": "panda0", "mode": "unknown", "channel": None, "error": "iw not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "iface": "panda0", "mode": "unknown", "channel": None, "error": "timeout"}


@router.post("/api/interface/monitor")
async def interface_monitor(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    canal = str(body.get("canal", 6))
    try:
        proc = await asyncio.create_subprocess_exec(
            "sudo", "-n", "bash", str(_MONITOR_SCRIPT), "panda0", canal,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode != 0:
            err = (stdout + stderr).decode(errors="replace")
            return JSONResponse({"ok": False, "error": err}, status_code=500)
        return JSONResponse({"ok": True, "mode": "monitor"})
    except asyncio.TimeoutError:
        return JSONResponse({"ok": False, "error": "Script timeout — check /etc/sudoers.d/warden"}, status_code=500)


@router.post("/api/interface/managed")
async def interface_managed() -> JSONResponse:
    try:
        proc = await asyncio.create_subprocess_exec(
            "sudo", "-n", "bash", "-c",
            "ip link set panda0 down && iw dev panda0 set type managed && ip link set panda0 up",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
        if proc.returncode != 0:
            err = (stdout + stderr).decode(errors="replace")
            return JSONResponse({"ok": False, "error": err}, status_code=500)
        return JSONResponse({"ok": True, "mode": "managed"})
    except asyncio.TimeoutError:
        return JSONResponse({"ok": False, "error": "Script timeout — check /etc/sudoers.d/warden"}, status_code=500)
