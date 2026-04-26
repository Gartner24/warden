# API: ESP32 REST

Source: `deliverables/warden-design.tex` (`\subsection{Diseño de la API REST de la ESP32}`)

Base URL: `http://192.168.4.1` (operator laptop must be joined to `WARDEN_CONTROL`)

All request and response bodies are JSON. Errors use standard HTTP codes (400, 403, 409) with a body `{ "error": "...", "codigo": "..." }`. No authentication beyond network membership on `WARDEN_CONTROL`.

---

## GET /status

Returns the current firmware state. Used by the Attacker Panel to verify connectivity and read live counters.

**Response 200 OK:**
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

`estado_cadena` values: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO`

---

## GET /attack/status

Returns the live execution state of the offensive chain. Designed for high-frequency polling by the Attacker Panel during an active attack (typical interval: 1 second, per UC-17). Use `GET /status` for general firmware state instead.

**Response 200 OK** (attack in progress):
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

`fase_actual` values: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO`

**Response 200 OK** (no attack running):
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

---

## GET /scan

Runs an active 2.4 GHz WiFi scan. Blocking for approximately 10 seconds.

**Response 200 OK:**
```json
{
  "duracion_seg": 10,
  "redes_encontradas": 8,
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

---

## GET /clients

Passively captures frames addressed to a target BSSID and returns detected client MACs. Blocking for `duration` seconds (default 30).

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `bssid` | string | yes | Target AP MAC (`XX:XX:XX:XX:XX:XX`) |
| `duration` | integer | no | Capture duration in seconds (default: 30) |

**Response 200 OK:**
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

**Response 400 Bad Request:**
```json
{
  "error": "BSSID requerido y debe tener formato XX:XX:XX:XX:XX:XX"
}
```

---

## GET /oui-lookup

Queries the OUI database embedded in flash and returns the manufacturer for a given MAC.

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `mac` | string | yes | MAC address to look up (`XX:XX:XX:XX:XX:XX`) |

**Response 200 OK (found):**
```json
{
  "mac": "9c:ef:d5:f7:5a:e5",
  "oui": "9c:ef:d5",
  "fabricante": "Panda Wireless, Inc.",
  "encontrado": true
}
```

**Response 200 OK (not found):**
```json
{
  "mac": "11:22:33:44:55:66",
  "oui": "11:22:33",
  "fabricante": "Fabricante desconocido",
  "encontrado": false
}
```

---

## GET /config

Returns the current `WardenConfig` fields.

**Response 200 OK:**
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

---

## POST /config

Updates the `WardenConfig`. Passes through the Ethical Validator before applying.

**Request body:**
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

**Response 200 OK:**
```json
{
  "ok": true,
  "config": { "...echo of applied config..." }
}
```

**Response 403 Forbidden** (Ethical Validator rejected):
```json
{
  "ok": false,
  "error": "BSSID en lista negra de OUIs externos. Configuracion rechazada.",
  "codigo": "ETHICAL_VALIDATOR_REJECTED"
}
```

---

## POST /attack/start

Starts the offensive chain with the current config. Re-invokes the Ethical Validator before starting.

**Request body:**
```json
{
  "modo": "cadena_automatica"
}
```

`modo` values: `cadena_automatica | beacon | deauth | eviltwin`

**Response 200 OK:**
```json
{
  "ok": true,
  "ataque_iniciado": "cadena_automatica",
  "fase_inicial": "FASE_1"
}
```

**Response 403 Forbidden:**
```json
{
  "ok": false,
  "error": "Configuracion no autorizada por validador etico"
}
```

**Response 409 Conflict** (attack already running):
```json
{
  "ok": false,
  "error": "Hay un ataque en curso. Detenga primero con POST /attack/stop"
}
```

---

## POST /attack/stop

Aborts the current phase and returns to idle.

**Response 200 OK** (attack was running):
```json
{
  "ok": true,
  "fase_detenida": "FASE_2",
  "duracion_seg": 47.3
}
```

**Response 200 OK** (no attack running):
```json
{
  "ok": true,
  "fase_detenida": null,
  "mensaje": "No habia ataque en curso"
}
```

---

## GET /credentials

Returns credentials captured during the current session (volatile RAM buffer — lost on reset).

**Response 200 OK:**
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

---

## GET /events

Server-Sent Events stream for real-time panel updates without aggressive polling (`Content-Type: text/event-stream`).

**Response (continuous stream):**
```
event: phase_change
data: {"fase": "FASE_2", "timestamp_ms": 30123}

event: client_connected
data: {"mac": "9c:ef:d5:f7:5a:e5", "ip": "10.0.0.12", "timestamp_ms": 145600}

event: credential_captured
data: {"usuario": "demo.user@warden.test", "ip": "10.0.0.12", "timestamp_ms": 145890}

event: phase_change
data: {"fase": "FINALIZADO", "timestamp_ms": 223456}
```

