"""Defender Panel REST API routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from detector.config import ConfigError, DetectorConfig
from detector.web.detector_runner import RunnerStateError

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
    return JSONResponse({"ok": True, "mensaje": f"Detector iniciado en {iface} canal {canal}."})


@router.post("/api/detector/stop")
async def detector_stop(request: Request) -> dict[str, Any]:
    runner = _runner(request)
    runner.stop()
    return {"ok": True, "mensaje": "Detector detenido."}
