"""Mock ESP32 for offline Attacker Panel development.
Routes match docs/internal/CANONICAL_API.md exactly.
"""
import json
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

FIX = Path(__file__).parent / "fixtures"
app = FastAPI(title="WARDEN Mock ESP32")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

_state = {"attack_running": False, "started_ms": 0}


def _load(name: str) -> dict:
    return json.loads((FIX / f"{name}.json").read_text())


@app.get("/status")
def status():
    return _load("status")


@app.get("/attack/status")
def attack_status():
    name = "attack-status-running" if _state["attack_running"] else "attack-status-idle"
    return _load(name)


@app.get("/scan")
def scan():
    time.sleep(0.5)
    return _load("scan")


@app.get("/clients")
def clients(bssid: str, duration: int = 30):
    if len(bssid) != 17:
        raise HTTPException(
            400,
            detail={"ok": False, "error": "BSSID requerido y debe tener formato XX:XX:XX:XX:XX:XX", "codigo": "INVALID_BSSID"},
        )
    return _load("clients")


@app.get("/oui-lookup")
def oui_lookup(mac: str):
    if mac.upper().startswith("9C:EF:D5"):
        return _load("oui-lookup-found")
    return _load("oui-lookup-not-found")


@app.get("/config")
def get_config():
    return _load("config")


@app.post("/config")
async def post_config(req: Request):
    return _load("config")


@app.post("/attack/start")
async def attack_start(req: Request):
    body = await req.json()
    if body.get("modo") not in ("cadena_automatica", "beacon", "deauth", "eviltwin"):
        return JSONResponse(_load("attack-start-403"), status_code=403)
    _state["attack_running"] = True
    _state["started_ms"] = int(time.time() * 1000)
    return _load("attack-start-ok")


@app.post("/attack/stop")
def attack_stop():
    _state["attack_running"] = False
    return {"ok": True, "fase_detenida": "FASE_2", "duracion_seg": 12.5}


@app.get("/credentials")
def credentials():
    return _load("credentials")
