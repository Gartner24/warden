# CANONICAL API CONTRACT — WARDEN

**Authority:** This document supersedes all other API descriptions when conflicts arise.
See footer for superseded sources.

**Last reconciled:** 2026-05-06

---

## ESP32 REST

Base URL: `http://192.168.4.1`

All bodies are JSON. No authentication beyond network membership on `WARDEN_CONTROL`.

### Error response shape

```json
{
  "ok": false,
  "error": "<human readable message>",
  "codigo": "<MACHINE_CODE>"
}
```

`codigo` values:

| Code | Trigger |
|---|---|
| `ETHICAL_VALIDATOR_REJECTED` | Config or attack blocked by ethical validator |
| `INVALID_BSSID` | BSSID missing or malformed |
| `ATTACK_ALREADY_RUNNING` | POST /attack/start while attack is active |
| `INVALID_CHANNEL` | Channel out of valid range |

### Success response shape

All mutating endpoints wrap their payload in `{ "ok": true, ... }`.
Read-only endpoints return the resource directly (no `ok` wrapper).

---

## GET /status

Returns current firmware state. Used by the Attacker Panel to verify connectivity and read live counters.

### Request

No parameters.

### Success Response

HTTP 200

```json
{
  "estado_cadena": "IDLE",
  "fase_inicio_ms": 0,
  "uptime_ms": 543210,
  "contadores": {
    "beacons_emitidos": 0,
    "deauths_emitidos": 0,
    "clientes_evil_twin": 0,
    "credenciales_capturadas": 0
  },
  "ataque_activo": false
}
```

`estado_cadena` enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO`

### Error Responses

None. Always returns 200.

---

## GET /attack/status

Returns live execution state of the offensive chain. Designed for high-frequency polling during an active attack (typical interval: 1 s). Use `GET /status` for general firmware state.

### Request

No parameters.

### Success Response

HTTP 200 (attack in progress):

```json
{
  "ataque_activo": true,
  "fase_actual": "FASE_2",
  "tiempo_transcurrido_seg": 47.3,
  "tiempo_restante_fase_seg": 12.7,
  "contadores": {
    "beacons_emitidos": 1500,
    "deauths_emitidos": 234,
    "clientes_evil_twin": 0,
    "credenciales_capturadas": 0
  }
}
```

HTTP 200 (no attack running):

```json
{
  "ataque_activo": false,
  "fase_actual": "IDLE",
  "tiempo_transcurrido_seg": 0,
  "tiempo_restante_fase_seg": 0,
  "contadores": {
    "beacons_emitidos": 0,
    "deauths_emitidos": 0,
    "clientes_evil_twin": 0,
    "credenciales_capturadas": 0
  }
}
```

`fase_actual` enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO`

### Error Responses

None. Always returns 200.

---

## GET /scan

Runs an active 2.4 GHz Wi-Fi scan. Blocking for approximately 10 seconds.

### Request

No parameters.

### Success Response

HTTP 200:

```json
{
  "duracion_seg": 10,
  "redes_encontradas": 2,
  "redes": [
    {
      "ssid": "LAB_WARDEN_UTP",
      "bssid": "e4:ab:89:d6:9b:80",
      "canal": 6,
      "rssi_dbm": -42,
      "cifrado": "WPA2"
    },
    {
      "ssid": "VECINO_WIFI",
      "bssid": "aa:bb:cc:dd:ee:ff",
      "canal": 11,
      "rssi_dbm": -78,
      "cifrado": "WPA2"
    }
  ]
}
```

Field note: `rssi_dbm` (not `rssi`). The bare `rssi` variant in design.tex is rejected.

### Error Responses

None. Always returns 200 (empty `redes` array if no networks found).

---

## GET /clients

Passively captures frames addressed to a target BSSID and returns detected client MACs. Blocking for `duration` seconds.

### Request

Query parameters:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `bssid` | string | yes | - | Target AP MAC (`XX:XX:XX:XX:XX:XX`) |
| `duration` | integer | no | 30 | Capture duration in seconds |

### Success Response

HTTP 200:

```json
{
  "bssid_objetivo": "e4:ab:89:d6:9b:80",
  "duracion_captura_seg": 30,
  "clientes_detectados": 2,
  "clientes": [
    {
      "mac": "9c:ef:d5:f7:5a:e5",
      "frames_observados": 47,
      "primer_frame_ms": 1234,
      "ultimo_frame_ms": 28876
    },
    {
      "mac": "ac:5f:3e:11:22:33",
      "frames_observados": 12,
      "primer_frame_ms": 5678,
      "ultimo_frame_ms": 27432
    }
  ]
}
```

Client object shape: `{mac, frames_observados, primer_frame_ms, ultimo_frame_ms}`.
The `rssi_promedio` variant in design.tex is rejected.

### Error Responses

HTTP 400:

```json
{
  "ok": false,
  "error": "BSSID requerido y debe tener formato XX:XX:XX:XX:XX:XX",
  "codigo": "INVALID_BSSID"
}
```

---

## GET /oui-lookup

Queries the OUI database embedded in flash and returns the manufacturer for a given MAC.

### Request

Query parameters:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `mac` | string | yes | MAC address (`XX:XX:XX:XX:XX:XX`) |

### Success Response

HTTP 200 (found):

```json
{
  "mac": "9c:ef:d5:f7:5a:e5",
  "oui": "9c:ef:d5",
  "fabricante": "Panda Wireless, Inc.",
  "encontrado": true
}
```

HTTP 200 (not found):

```json
{
  "mac": "11:22:33:44:55:66",
  "oui": "11:22:33",
  "fabricante": "Fabricante desconocido",
  "encontrado": false
}
```

OUI test fixture: `9C:EF:D5:F7:5A:E5` -> `"Panda Wireless, Inc."` (verified against IEEE OUI registry).
The Xiaomi variant and `fabricante: null` shape in design.tex are rejected.

### Error Responses

None. Always returns 200 with `encontrado: false` when MAC is unknown.

---

## GET /config

Returns the current `WardenConfig` fields.

### Request

No parameters.

### Success Response

HTTP 200:

```json
{
  "bssid_objetivo": "e4:ab:89:d6:9b:80",
  "mac_victima": "9c:ef:d5:f7:5a:e5",
  "ssid_clonar": "LAB_WARDEN_UTP",
  "canal": 6,
  "duraciones_seg": {
    "beacon_flood": 30,
    "deauth": 15,
    "evil_twin": 120
  }
}
```

### Error Responses

None. Always returns 200.

---

## POST /config

Updates the `WardenConfig`. Passes through the Ethical Validator before applying.

### Request

Body:

```json
{
  "bssid_objetivo": "e4:ab:89:d6:9b:80",
  "mac_victima": "9c:ef:d5:f7:5a:e5",
  "ssid_clonar": "LAB_WARDEN_UTP",
  "canal": 6,
  "duraciones_seg": {
    "beacon_flood": 30,
    "deauth": 15,
    "evil_twin": 120
  }
}
```

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "config": {
    "bssid_objetivo": "e4:ab:89:d6:9b:80",
    "mac_victima": "9c:ef:d5:f7:5a:e5",
    "ssid_clonar": "LAB_WARDEN_UTP",
    "canal": 6,
    "duraciones_seg": {
      "beacon_flood": 30,
      "deauth": 15,
      "evil_twin": 120
    }
  }
}
```

### Error Responses

HTTP 403 — Ethical Validator rejected:

```json
{
  "ok": false,
  "error": "BSSID en lista negra de OUIs externos. Configuracion rechazada.",
  "codigo": "ETHICAL_VALIDATOR_REJECTED"
}
```

HTTP 400 — Invalid channel:

```json
{
  "ok": false,
  "error": "Canal fuera de rango valido (1-13).",
  "codigo": "INVALID_CHANNEL"
}
```

---

## POST /attack/start

Starts the offensive chain with the current config. Re-invokes the Ethical Validator before starting.

### Request

Body:

```json
{
  "modo": "cadena_automatica"
}
```

`modo` enum: `cadena_automatica | beacon | deauth | eviltwin`

The `cadena_completa` and `solo_*` variants in design.tex are rejected.

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "ataque_iniciado": "cadena_automatica",
  "fase_inicial": "FASE_1"
}
```

### Error Responses

HTTP 403 — Ethical Validator rejected:

```json
{
  "ok": false,
  "error": "Configuracion no autorizada por validador etico.",
  "codigo": "ETHICAL_VALIDATOR_REJECTED"
}
```

HTTP 409 — Attack already running:

```json
{
  "ok": false,
  "error": "Hay un ataque en curso. Detenga primero con POST /attack/stop.",
  "codigo": "ATTACK_ALREADY_RUNNING"
}
```

---

## POST /attack/stop

Aborts the current phase and returns to idle.

### Request

No body required.

### Success Response

HTTP 200 (attack was running):

```json
{
  "ok": true,
  "fase_detenida": "FASE_2",
  "duracion_seg": 47.3
}
```

HTTP 200 (no attack running):

```json
{
  "ok": true,
  "fase_detenida": null,
  "mensaje": "No habia ataque en curso."
}
```

### Error Responses

None. Always returns 200.

---

## GET /credentials

Returns credentials captured during the current session (volatile RAM buffer — lost on reset).

### Request

No parameters.

### Success Response

HTTP 200:

```json
{
  "total": 2,
  "credenciales": [
    {
      "timestamp_ms": 187432,
      "cliente_ip": "10.0.0.12",
      "usuario": "demo.user@warden.test",
      "password": "demo-password-12345"
    },
    {
      "timestamp_ms": 195203,
      "cliente_ip": "10.0.0.13",
      "usuario": "test@example.com",
      "password": "test123"
    }
  ]
}
```

### Error Responses

None. Always returns 200 (empty `credenciales` array if none captured).

---

## GET /events

Server-Sent Events stream for real-time panel updates (`Content-Type: text/event-stream`).

### Request

No parameters. Connection stays open until client closes.

### Message Types

**phase_change** — emitted when the offensive chain transitions to a new phase:

```
event: phase_change
data: {"fase": "FASE_2", "timestamp_ms": 30123}
```

**client_connected** — emitted when a client associates to the Evil Twin AP:

```
event: client_connected
data: {"mac": "9c:ef:d5:f7:5a:e5", "ip": "10.0.0.12", "timestamp_ms": 145600}
```

**credential_captured** — emitted when the captive portal intercepts a credential submission:

```
event: credential_captured
data: {"usuario": "demo.user@warden.test", "ip": "10.0.0.12", "timestamp_ms": 145890}
```

Event names are English strings. Payload keys are Spanish. This is intentional.

### Error Responses

HTTP 503 if the SSE subsystem is unavailable. Client should reconnect with exponential backoff.

---

## Detector REST

Base URL: `http://127.0.0.1:8000` (local only by default)

All bodies are JSON.

### Detector error codes

| Code | Trigger |
|---|---|
| `DETECTOR_ALREADY_RUNNING` | POST /api/detector/start while detector is running |
| `DETECTOR_NOT_RUNNING` | POST /api/detector/stop while detector is stopped |
| `INVALID_BSSID` | Malformed BSSID in start body |
| `INVALID_CHANNEL` | Channel out of range 1-13 |

---

## GET /api/status

Returns current session state: running flag, alert counts, uptime.

### Request

No parameters.

### Success Response

HTTP 200:

```json
{
  "detector_corriendo": false,
  "duracion_seg": 0,
  "frames_procesados": 0,
  "alertas_totales": 0,
  "alertas_por_tipo": {
    "BEACON_FLOOD": 0,
    "DEAUTH": 0,
    "EVIL_TWIN": 0,
    "CADENA_OFENSIVA": 0
  }
}
```

### Error Responses

None. Always returns 200.

---

## POST /api/session/reset

Clears all analyzer state and counters; restarts the session. Broadcasts a `session_reset` message to all connected WebSocket clients.

### Request

No body required.

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "mensaje": "Sesion reiniciada."
}
```

### Error Responses

None. Always returns 200.

---

## GET /api/config

Reads current detection thresholds.

### Request

No parameters.

### Success Response

HTTP 200:

```json
{
  "umbrales": {
    "beacon_flood_bssids_por_seg": 30,
    "deauth_frames_por_seg": 5,
    "evil_twin_umbral_similitud": 0.85
  },
  "canal": 6,
  "bssid_protegido": "e4:ab:89:d6:9b:80",
  "ssid_protegido": "LAB_WARDEN_UTP"
}
```

### Error Responses

None. Always returns 200.

---

## POST /api/config

Updates detection thresholds at runtime.

### Request

Body:

```json
{
  "umbrales": {
    "beacon_flood_bssids_por_seg": 30,
    "deauth_frames_por_seg": 5,
    "evil_twin_umbral_similitud": 0.85
  },
  "canal": 6,
  "bssid_protegido": "e4:ab:89:d6:9b:80",
  "ssid_protegido": "LAB_WARDEN_UTP"
}
```

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "config": {
    "umbrales": {
      "beacon_flood_bssids_por_seg": 30,
      "deauth_frames_por_seg": 5,
      "evil_twin_umbral_similitud": 0.85
    },
    "canal": 6,
    "bssid_protegido": "e4:ab:89:d6:9b:80",
    "ssid_protegido": "LAB_WARDEN_UTP"
  }
}
```

### Error Responses

HTTP 422 — Invalid threshold values (standard FastAPI validation error body).

---

## POST /api/detector/start

Starts the detector with the specified interface and target network parameters.

### Request

Body:

```json
{
  "iface": "wlan0mon",
  "canal": 6,
  "bssid_protegido": "e4:ab:89:d6:9b:80",
  "ssid_protegido": "LAB_WARDEN_UTP",
  "umbrales": {
    "beacon_flood_bssids_por_seg": 30,
    "deauth_frames_por_seg": 5,
    "evil_twin_umbral_similitud": 0.85
  }
}
```

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "mensaje": "Detector iniciado en wlan0mon canal 6."
}
```

### Error Responses

HTTP 409 — Detector already running:

```json
{
  "ok": false,
  "error": "El detector ya esta en ejecucion.",
  "codigo": "DETECTOR_ALREADY_RUNNING"
}
```

---

## POST /api/detector/stop

Stops the running detector.

### Request

No body required.

### Success Response

HTTP 200:

```json
{
  "ok": true,
  "mensaje": "Detector detenido."
}
```

### Error Responses

None. Always returns 200 (idempotent).

---

## Detector WebSocket

Endpoint: `ws://127.0.0.1:8000/ws`

The server pushes JSON events to all connected clients. Clients may send command messages.
All messages are JSON objects with a `tipo` or `comando` discriminator.

---

### Server-push messages

#### init

Sent immediately on connection.

```json
{
  "tipo": "init",
  "alertas_recientes": [],
  "frames_procesados": 0,
  "detector_corriendo": false
}
```

`alertas_recientes` is an array of `alerta` payloads (see below) from the current session.

#### alerta

Sent when the detector raises a new alert.

```json
{
  "tipo": "alerta",
  "severidad": "CRITICAL",
  "tipo_alerta": "EVIL_TWIN",
  "mensaje": "Posible Evil Twin detectado en canal 6.",
  "timestamp": "2026-01-01T12:00:00+00:00",
  "detalles": {}
}
```

`severidad` enum: `INFO | WARNING | ALERT | CRITICAL`

`tipo_alerta` enum: `BEACON_FLOOD | DEAUTH | EVIL_TWIN | CADENA_OFENSIVA`

`timestamp` format: ISO 8601 with UTC offset.

`detalles` is an object with alert-specific fields (may be empty `{}`).

Example with detalles populated (BEACON_FLOOD):

```json
{
  "tipo": "alerta",
  "severidad": "ALERT",
  "tipo_alerta": "BEACON_FLOOD",
  "mensaje": "Tasa anomala de beacons: 87.4 BSSIDs unicos/s.",
  "timestamp": "2026-01-01T12:00:00+00:00",
  "detalles": {
    "bssids_unicos": 437,
    "ventana_seg": 5
  }
}
```

#### session_reset

Broadcast to all connected clients after `POST /api/session/reset` completes.

```json
{
  "tipo": "session_reset"
}
```

#### detector_status

Sent when the detector starts, stops, or encounters an error.

```json
{
  "tipo": "detector_status",
  "estado": "corriendo",
  "mensaje": "Detector iniciado en wlan0mon canal 6."
}
```

`estado` enum: `corriendo | detenido | error`

---

### Client-push messages

#### status

Request a snapshot of the current detector state. Server responds with a `detector_status` message.

```json
{
  "comando": "status"
}
```

#### ping

Keepalive. Server does not reply.

```json
{
  "comando": "ping"
}
```

---

## Reconciliation Notes

The following inconsistencies were found across source documents and resolved here:

| Field / endpoint | design.tex variant (rejected) | Canonical value |
|---|---|---|
| `/status` shape | `{"modo": "control", ...}` flat structure | `{estado_cadena, fase_inicio_ms, uptime_ms, contadores{...}, ataque_activo}` |
| `/scan` RSSI field | `rssi` | `rssi_dbm` |
| `/clients` client object | `{mac, frames_observados, rssi_promedio}` | `{mac, frames_observados, primer_frame_ms, ultimo_frame_ms}` |
| `/oui-lookup` not-found shape | `{"fabricante": null, "encontrado": false}` (no `oui` field) | `{mac, oui, fabricante: "Fabricante desconocido", encontrado: false}` |
| `/oui-lookup` OUI test fixture | MAC `9C:EF:D5:...` -> Xiaomi | MAC `9C:EF:D5:F7:5A:E5` -> "Panda Wireless, Inc." |
| `/attack/start` modo values | `cadena_completa \| solo_beacon \| solo_deauth \| solo_eviltwin` | `cadena_automatica \| beacon \| deauth \| eviltwin` |
| Error response wrapper | `{"error": "...", "codigo": "..."}` (no `ok` field) | `{"ok": false, "error": "...", "codigo": "..."}` |
| Detector WS `init` shape | `{"tipo": "init", "alertas_recientes": [], "estado": "conectado"}` | `{"tipo": "init", "alertas_recientes": [], "frames_procesados": 0, "detector_corriendo": false}` |
| Detector WS `alerta` shape | Nested under `datos` key | Flat (all fields at top level alongside `tipo`) |
| Detector `POST /api/detector/start` field `channel` | `channel` (English, from detector-fastapi.md) | `canal` (Spanish, consistent with project JSON field naming convention) |
| `GET /api/status` field `duracion_seg` | `uptime_seg` (introduced during drafting; no source basis) | `duracion_seg` (matches design.tex routes.py) |
| `GET /api/status` field `alertas_por_tipo` | absent from design.tex | Added intentionally: Reporter tracks per-type counters; this field exposes them. Not in any source doc — this is a canonical addition. |

---

## Supersedes

This document supersedes the following when conflicts arise:

- `docs/api/esp32-rest.md`
- `docs/api/detector-fastapi.md`
- `deliverables/warden-design.tex` (sections: Diseno de la API REST de la ESP32, Esquemas JSON)

`CANONICAL_API.md` is the single authoritative source for all WARDEN API contracts.
