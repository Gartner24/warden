# WARDEN JSON Field Glossary

> This glossary is for developers implementing code from CANONICAL_API.md. Spanish is authoritative - English meanings are for comprehension only.

| Spanish | English | Type | Notes |
|---|---|---|---|
| `alertas_por_tipo` | alerts by type | object | Map of alert type string to integer count; keys: `BEACON_FLOOD`, `DEAUTH`, `EVIL_TWIN`, `CADENA_OFENSIVA` |
| `alertas_recientes` | recent alerts | array of alert objects | Included in WS `init` message; contains `alerta` payloads from the current session |
| `alertas_totales` | total alerts | integer | Cumulative alert count for the current session |
| `ataque_activo` | attack active | boolean | True when any phase of the offensive chain is running |
| `ataque_detenido` | attack stopped | string or null | Reflected back by `POST /attack/stop`; not a standalone field in responses |
| `ataque_iniciado` | attack initiated | string | Value of `modo` echoed back in `POST /attack/start` success response |
| `beacon_flood` | beacon flood duration | integer | Key inside `duraciones_seg`; seconds to run beacon flood (Phase 1) |
| `beacon_flood_bssids_por_seg` | beacon flood BSSIDs per second | integer | Key inside `umbrales`; threshold for BEACON_FLOOD alert |
| `beacons_emitidos` | beacons emitted | integer | Key inside `contadores`; count of beacon frames transmitted |
| `beacons_por_segundo` | beacons per second | integer | Rate of beacon frame emission; referenced in design docs |
| `bssid` | BSSID | string | MAC address of an access point; format `XX:XX:XX:XX:XX:XX` |
| `bssid_objetivo` | target BSSID | string | MAC of the AP being attacked or monitored; format `XX:XX:XX:XX:XX:XX` |
| `bssid_protegido` | protected BSSID | string | MAC of the legitimate AP the detector is guarding; format `XX:XX:XX:XX:XX:XX` |
| `bssid_validado` | validated BSSID | boolean | Indicates BSSID passed ethical validator checks |
| `bssids_unicos` | unique BSSIDs | integer | Key inside `detalles` of a BEACON_FLOOD alert; count of unique BSSIDs seen |
| `canal` | channel | integer | Wi-Fi channel number (1-13) |
| `cifrado` | encryption | string | Wi-Fi security type, e.g. `WPA2` |
| `cliente_ip` | client IP | string | IP address of a captive-portal client; IPv4 dotted-decimal |
| `clientes` | clients | array of client objects | List of detected client stations; each has `{mac, frames_observados, primer_frame_ms, ultimo_frame_ms}` |
| `clientes_detectados` | clients detected | integer | Count of unique client MACs captured during `GET /clients` |
| `clientes_evil_twin` | evil twin clients | integer | Key inside `contadores`; count of clients associated to the evil twin AP |
| `codigo` | error code | string | Machine-readable error identifier in error responses, e.g. `INVALID_BSSID` |
| `comando` | command | string | Discriminator field in client-push WS messages; e.g. `status`, `ping` |
| `config` | config | object | Echoed `WardenConfig` object inside `POST /config` and `POST /api/config` success responses |
| `contadores` | counters | object | Nested object with runtime counters: `beacons_emitidos`, `deauths_emitidos`, `clientes_evil_twin`, `credenciales_capturadas` |
| `credenciales` | credentials | array of credential objects | List of captured credentials; each has `{timestamp_ms, cliente_ip, usuario, password}` |
| `credenciales_capturadas` | credentials captured | integer | Key inside `contadores`; count of credential submissions intercepted |
| `deauth` | deauth duration | integer | Key inside `duraciones_seg`; seconds to run deauthentication phase (Phase 2) |
| `deauth_frames_por_seg` | deauth frames per second | integer | Key inside `umbrales`; threshold for DEAUTH alert |
| `deauths_emitidos` | deauths emitted | integer | Key inside `contadores`; count of deauthentication frames transmitted |
| `detalles` | details | object | Alert-specific extra fields inside an `alerta` WS message; may be empty `{}` |
| `detector_corriendo` | detector running | boolean | True when the detector background task is active |
| `duracion_beacon_flood` | beacon flood duration | integer | Seconds allocated to Phase 1; referenced in config contexts |
| `duracion_captura_seg` | capture duration (seconds) | integer | Duration of the passive frame capture in `GET /clients` response |
| `duracion_corriendo_seg` | running duration (seconds) | number | How long the detector has been running; referenced in detector status contexts |
| `duracion_deauth` | deauth duration | integer | Seconds allocated to Phase 2; referenced in config contexts |
| `duracion_evil_twin` | evil twin duration | integer | Seconds allocated to Phase 3; referenced in config contexts |
| `duracion_seg` | duration (seconds) | number | General-purpose elapsed or configured duration field; context-dependent (scan duration, stop duration, detector uptime) |
| `duraciones_seg` | durations (seconds) | object | Nested object holding per-phase durations: `beacon_flood`, `deauth`, `evil_twin` |
| `encontrado` | found | boolean | True if OUI lookup matched a known manufacturer |
| `error` | error | string | Human-readable error description in error responses |
| `estado` | state | string | Discriminator in `detector_status` WS message; enum: `corriendo | detenido | error` |
| `estado_cadena` | chain state | string | Firmware-level attack chain state; enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO` |
| `evil_twin` | evil twin duration | integer | Key inside `duraciones_seg`; seconds to run evil twin phase (Phase 3) |
| `evil_twin_umbral_similitud` | evil twin similarity threshold | float | Key inside `umbrales`; minimum SSID similarity score to trigger EVIL_TWIN alert (0.0-1.0) |
| `fabricante` | manufacturer | string | OUI-resolved manufacturer name; `"Fabricante desconocido"` when not found |
| `fase` | phase | string | Current phase identifier in SSE `phase_change` event; enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO` |
| `fase_actual` | current phase | string | Active phase reported by `GET /attack/status`; enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO` |
| `fase_detenida` | stopped phase | string or null | Phase that was aborted by `POST /attack/stop`; null if no attack was running |
| `fase_inicial` | initial phase | string | First phase of the chain echoed in `POST /attack/start` success response |
| `fase_inicio_ms` | phase start timestamp (ms) | integer | Millisecond uptime timestamp when the current phase began; 0 when idle |
| `frames_observados` | frames observed | integer | Count of 802.11 frames seen from a specific client MAC during capture |
| `frames_procesados` | frames processed | integer | Total 802.11 frames analyzed by the detector in the current session |
| `iface` | interface | string | Network interface name for monitor mode, e.g. `wlan0mon` |
| `ip` | IP address | string | Client IP in SSE `client_connected` event |
| `mac` | MAC address | string | Hardware address of a client or AP; format `XX:XX:XX:XX:XX:XX` |
| `mac_victima` | victim MAC | string | MAC of the target client station; format `XX:XX:XX:XX:XX:XX` |
| `mensaje` | message | string | Human-readable status or error text; used in several response shapes and WS messages |
| `modo` | mode | string | Attack mode in `POST /attack/start` body; enum: `cadena_automatica | beacon | deauth | eviltwin` |
| `ok` | ok | boolean | Top-level success flag in mutating endpoint responses; `true` on success, `false` on error |
| `oui` | OUI | string | First 3 octets of a MAC address identifying the manufacturer; format `XX:XX:XX` |
| `password` | password | string | Captured Wi-Fi or portal password from a credential submission |
| `prefijo_ssid_falso` | fake SSID prefix | string | Prefix prepended to cloned SSID for evil twin beacons; referenced in design docs |
| `primer_frame_ms` | first frame timestamp (ms) | integer | Uptime millisecond timestamp of the first frame observed from a client |
| `redes` | networks | array of network objects | List of APs found by `GET /scan`; each has `{ssid, bssid, canal, rssi_dbm, cifrado}` |
| `redes_encontradas` | networks found | integer | Count of APs returned by `GET /scan` |
| `rssi_dbm` | RSSI (dBm) | integer | Signal strength in dBm; negative values; use this, not bare `rssi` |
| `severidad` | severity | string | Alert severity level; enum: `INFO | WARNING | ALERT | CRITICAL` |
| `ssid` | SSID | string | Network name of a scanned AP |
| `ssid_clonar` | SSID to clone | string | Name of the legitimate network to impersonate in the evil twin |
| `ssid_objetivo` | target SSID | string | SSID of the network being targeted; used in detection and config contexts |
| `ssid_protegido` | protected SSID | string | SSID of the legitimate AP the detector is guarding |
| `tiempo_restante_fase_seg` | time remaining in phase (seconds) | number | Seconds until the current phase completes; 0 when idle |
| `tiempo_transcurrido_seg` | time elapsed in phase (seconds) | number | Seconds since the current phase started; 0 when idle |
| `timestamp` | timestamp | string | ISO 8601 datetime with UTC offset; used in WS `alerta` messages |
| `timestamp_ms` | timestamp (ms) | integer | Uptime millisecond timestamp; used in SSE events and credential records |
| `tipo` | type | string | Message type discriminator in server-push WS messages; e.g. `init`, `alerta`, `session_reset`, `detector_status` |
| `tipo_alerta` | alert type | string | Alert category in WS `alerta` message; enum: `BEACON_FLOOD | DEAUTH | EVIL_TWIN | CADENA_OFENSIVA` |
| `total` | total | integer | Count of items in a collection; used in `GET /credentials` response |
| `ultimo_frame_ms` | last frame timestamp (ms) | integer | Uptime millisecond timestamp of the most recent frame observed from a client |
| `umbrales` | thresholds | object | Detection threshold configuration; contains `beacon_flood_bssids_por_seg`, `deauth_frames_por_seg`, `evil_twin_umbral_similitud` |
| `uptime_ms` | uptime (ms) | integer | Milliseconds since firmware boot; reported by `GET /status` |
| `usuario` | username | string | Captured username or email from a credential submission |
| `validador_etico` | ethical validator | object or boolean | Ethical validator state or configuration reference; blocks attacks targeting non-lab OUIs |
| `ventana_seg` | window (seconds) | integer | Key inside `detalles` of a BEACON_FLOOD alert; time window over which BSSIDs were counted |
