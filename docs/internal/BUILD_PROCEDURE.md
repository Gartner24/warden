# WARDEN Build Procedure

This document describes how the WARDEN system was designed and built from scratch,
phase by phase. It covers design decisions, tooling choices, and the order in which
each subsystem was implemented and verified.

---

## 1. Starting Point

The repository began as documentation only: LaTeX deliverables, architecture docs,
and a README. No executable code existed. Every line of source code was written
during the build phases described below.

The build follows an **offline-first** principle: all validation happens without
hardware. The ESP32 is tested via `arduino-cli` compile verification. The Python
detector is tested against synthetic PCAP files. Hardware is required only at
demo day (see `docs/internal/HARDWARE_BRINGUP.md`).

---

## 2. Phase 0 - Contracts and Scaffolding

Before writing any executable code, five internal reference documents were created
under `docs/internal/`. These prevent duplicate work and ensure every subsystem
speaks the same language.

| Document | Purpose |
|---|---|
| `CANONICAL_API.md` | Single source of truth for every REST/SSE/WebSocket schema. Resolves conflicts between the two API variant sources in the LaTeX deliverable. |
| `CONSTANTS.md` | All numeric constants: channels, IPs, timing defaults, detection thresholds, OUI test fixtures. |
| `GLOSSARY.md` | Spanish-to-English mapping of every JSON field name. |
| `UTILS_REGISTRY.md` | Index of shared helpers. Prevents the same function being written twice in different modules. |
| `FIRMWARE_RUNTIME.md` | FreeRTOS task table, Wi-Fi mode transition diagram, queue policy. |

The key API conflicts resolved in `CANONICAL_API.md`:

- `rssi` -> `rssi_dbm` (all scan results)
- `modo` enum locked to `cadena_automatica | beacon | deauth | eviltwin`
- `estado_cadena` enum: `IDLE | FASE_1 | FASE_2 | FASE_3 | FINALIZADO`
- `/clients` shape: `{mac, frames_observados, primer_frame_ms, ultimo_frame_ms}` (drops `rssi_promedio`)
- OUI test fixture: MAC `9C:EF:D5` -> "Panda Wireless, Inc." (locked against IEEE registry)
- Severity enum: `INFO | WARNING | ALERT | CRITICAL`
- Error shape: `{ok: false, error: "...", codigo: "MACHINE_CODE"}`

After the docs, the source tree was scaffolded:

```
src/attacker/         - ESP32 firmware (Arduino sketch)
src/attacker-panel/   - Operator static SPA
src/detector/         - Python detection engine
src/ethical_validator/- Host-buildable C++ validation library
tools/mock-esp32/     - FastAPI mock for offline panel development
scripts/              - Generator and utility scripts
tests/                - pytest test suite
```

Python tooling pinned: `scapy==2.5.0`, `fastapi==0.110.0`, `uvicorn==0.27.1`,
`pytest==8.1.1`, `ruff==0.3.4`, `mypy==1.9.0`.

A duplicate-helper enforcement test (`tests/test_no_duplicate_helpers.py`) and a
bash collision check (`scripts/check-cpp-helpers.sh`) were added at this stage.
They run in CI and fail the build if two modules export the same public symbol.

---

## 3. Phase 1 - Python Detector (strict TDD)

The detector was built module by module using red-green-refactor:

1. **`DetectorConfig`** - frozen dataclass with argparse CLI. Validates BSSID format,
   channel range, and --iface/--pcap mutual exclusion.

2. **`pcap_capture`** - reads 802.11 frames from a PCAP file via Scapy's `rdpcap`.

3. **`live_capture`** - wraps Scapy `sniff()` in a daemon thread. Constructor and
   lifecycle are tested without hardware (`iface="lo"`).

4. **`Dispatcher`** - routes a Scapy packet to analyzer callbacks. Beacon frames
   route to both `on_beacon` and `on_evil_twin`. Deauth frames route to `on_deauth`.
   Radiotap headers are transparent (Scapy handles layer stripping).

5. **`BeaconFloodAnalyzer`** (D-01) - sliding window over unique source BSSIDs.
   Fires `BEACON_FLOOD / ALERT` when beacons/sec >= threshold. Cooldown prevents
   repeated alerts within the refractory period.

6. **`DeauthAnalyzer`** (D-02) - same sliding-window pattern, counts deauth frames
   where `addr3 == bssid_protegido`. Fires `DEAUTH / ALERT`.

7. **`EvilTwinAnalyzer`** (D-03) - maintains a registry of `ssid -> set(bssids)`.
   When a beacon for `ssid_protegido` arrives from a BSSID that is not
   `bssid_protegido` and not in the whitelist, fires `EVIL_TWIN / CRITICAL`.
   Deduplicates per `(ssid, rogue_bssid)` pair.

8. **`ChainCorrelator`** - consumes alerts from all three analyzers. When
   `BEACON_FLOOD`, `DEAUTH`, and `EVIL_TWIN` all appear in ascending timestamp order
   within the `ventana_correlacion_seg` window, emits `CADENA_OFENSIVA / CRITICAL`
   once.

9. **`Reporter`** - prints to stdout and pushes to a bounded `asyncio.Queue(maxsize=2048)`.
   On full queue: drop oldest, enqueue newest. Logs a WARNING every 1000 drops.

10. **`Session`** - wraps Reporter, tracks `frames_procesados` and elapsed time.

11. **`main.py`** - wires the full pipeline. Timestamp passthrough uses a mutable
    list cell `_ts: list[datetime] = [...]` so analyzer lambdas always see the
    current packet time without modifying the Dispatcher interface.

---

## 4. Phase 1.5 - Ethical Validator (host-buildable C++)

The validator lives in `src/ethical_validator/` as a standalone CMake project with
no ESP-IDF or Arduino dependencies. It compiles on Linux with gcc/clang (C++17).

The API:

```cpp
ValidationResult validate_bssid(const uint8_t bssid[6],
                                 bool confirm_provided,
                                 const ValidatorConfig& cfg);
```

Check order (significant - lab router bypasses the ISP blacklist by design):

1. Broadcast (`FF:FF:FF:FF:FF:FF`) -> `REJECTED_BROADCAST`
2. Null (`00:00:00:00:00:00`) -> `REJECTED_NULL`
3. Exact match on `lab_router_bssid` -> `VALID` (unconditional trust)
4. OUI prefix in `isp_oui_blacklist` -> `REJECTED_OUI_BLACKLIST`
5. `confirm_provided == true` -> `VALID`
6. Otherwise -> `REQUIRES_CONFIRMATION`

Tested with doctest (7 cases + 1 null-guard edge case). The same `.h` and `.cpp`
files are copied into `src/attacker/` for the firmware build.

---

## 5. Phase 2 - PCAP Fixtures

`scripts/generate-fixtures.py` creates six deterministic synthetic PCAP files
(seeded RNG, RadioTap-prefixed, timestamps set manually):

| File | Content |
|---|---|
| `beacon-flood.pcap` | 200 unique BSSIDs over 4 seconds (40/s, above 30/s threshold) |
| `deauth.pcap` | 80 deauth frames to protected BSSID over 3 seconds |
| `evil-twin.pcap` | Single beacon from rogue BSSID cloning protected SSID |
| `chain.pcap` | All three phases in sequence within 30 seconds |
| `quiet.pcap` | 20 legitimate beacons from protected BSSID only, no attacks |
| `live-parity-radiotap.pcap` | 1 beacon + 1 deauth with RadioTap, used as hardware parity gate |

The fixtures are tracked in git (`.gitignore` has a `!tests/fixtures/pcap/*.pcap`
exception). Running `generate-fixtures.py` after cloning will regenerate them.

---

## 6. Phase 3 - Defender Panel (FastAPI + WebSocket)

The Defender Panel is a FastAPI server that:

1. Runs the detector in a background thread (`DetectorRunner`)
2. Drains alerts from a bounded `asyncio.Queue` in a lifespan coroutine
3. Broadcasts every alert to all connected WebSocket clients (`WebSocketManager`)
4. Exposes REST control endpoints at `/api/*`

Architecture:

```
HTTP client   ->  /api/detector/start  ->  DetectorRunner.start(config)
                                              |
                                    background thread
                                    iter_packets() or LiveCapture
                                    -> Dispatcher -> Analyzers -> Reporter
                                              |
                                    asyncio.Queue (maxsize=2048)
                                              |
                               lifespan coroutine _drain_queue()
                                              |
                               WebSocketManager.broadcast(alert)
                                              |
                               all connected /ws clients
```

The integration test (`tests/detector/web/test_server_integration.py`) starts the
full server, feeds `chain.pcap`, and verifies that all four alert types
(`BEACON_FLOOD`, `DEAUTH`, `EVIL_TWIN`, `CADENA_OFENSIVA`) are broadcast within
3 seconds.

The static Defender Panel UI (`src/detector/web/static/`) shows a color-coded
threat indicator (green / yellow / red driven by alert severity) and a live alert
list updated via WebSocket messages.

---

## 7. Phase 4 - ESP32 Firmware Foundation

The firmware is an Arduino-ESP32 sketch in `src/attacker/`. Key constraint: `arduino-cli`
does not auto-compile files in subdirectories, so all `.cpp` source files are
in the sketch root.

Build verified with:
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 src/attacker
```

Libraries used:
- `ESPAsyncWebServer` (patched for mbedtls 3.x: `_ret` suffix removed from MD5 calls)
- `AsyncTCP`
- `ArduinoJson 7`

The validator is integrated by copying `ethical_validator.h` and `.cpp` into the
sketch root. `config_set_bssid()` calls `warden::validate_bssid()` and only sets
`bssid_validado = true` when the result is `VALID`. All attack endpoints check
`bssid_validado` before proceeding.

---

## 8. Phase 5 - ESP32 REST API

All endpoints from `CANONICAL_API.md` implemented:

| Endpoint | Description |
|---|---|
| `GET /status` | Chain state, uptime, counters |
| `GET /attack/status` | Current phase, elapsed time |
| `GET /scan` | WiFi scan using `WiFi.scanNetworks()` |
| `GET /clients` | Promiscuous-mode client capture (stub, full impl needs hardware) |
| `GET /oui-lookup` | Binary search on 5500-entry PROGMEM OUI table |
| `GET /config` | Current WardenConfig values |
| `POST /config` | Update BSSID/SSID/channel, runs through validator |
| `POST /attack/start` | Starts chain controller if validator passed |
| `POST /attack/stop` | Stops chain and returns to IDLE |
| `GET /credentials` | Reads 16-slot circular credential buffer |
| `GET /events` | SSE stream for `phase_change`, `client_connected`, `credential_captured` |

The OUI database is generated from the IEEE registry CSV:
```bash
python3 scripts/generate-oui-db.py --input oui.csv --output src/attacker/oui_database.h --max 5500
```

---

## 9. Phase 6 - Attack Modules

Each attack module is a FreeRTOS task. Shared radio access is not explicitly
mutex-gated at the task level (each phase stops the previous one before starting).

| Module | FreeRTOS task | Core | Priority |
|---|---|---|---|
| `beacon_flood` | `beacon_emitter` | 1 | IDLE+4 |
| `deauth_module` | `deauth_emitter` | 1 | IDLE+4 |
| `evil_twin` | (no task - configures softAP directly) | - | - |
| `chain_controller` | `chain_ctrl` | 0 | IDLE+3 |

The `frame_builder` functions (`build_beacon_frame`, `build_deauth_frame`) are
pure C with no platform dependencies. They are host-tested with doctest against
hand-computed 802.11 frame layouts (frame control bytes, address fields, IEs).

The chain controller transitions:
```
IDLE -> FASE_1_BEACON (beacon flood for duracion_beacon seconds)
     -> FASE_2_DEAUTH (deauth for duracion_deauth seconds)
     -> FASE_3_EVIL   (evil twin for duracion_evil_twin seconds)
     -> FINALIZADO
```

Each transition emits an SSE `phase_change` event. `POST /attack/stop` at any
point sets `ataque_activo = false`, which causes the active task's `while` loop
to exit and self-delete.

---

## 10. Phase 7 - Attacker Panel

A static SPA served with `python3 -m http.server 8080` from `src/attacker-panel/`.
No build step, no bundler. Tailwind CSS loaded from CDN.

Four views, each re-rendered from scratch on navigation:

- **Recon** - calls `GET /scan`, renders network table, on row click calls
  `GET /clients`, inline OUI lookup via `GET /oui-lookup`.
- **Ethics** - shows selected target, displays warning, requires operator to type
  the word `confirm` in a text field before the "Launch" button is enabled. On
  submit, calls `POST /config` with `confirm_provided: true`.
- **Attack** - calls `POST /attack/start`, polls `GET /attack/status` every second,
  updates phase indicator and counters live, fetches credentials when count > 0.
  Navigates to Summary when `estado_cadena == FINALIZADO`.
- **Summary** - shows final counters and captured credentials, offers JSON export.

During development, `API_BASE` in `assets/api-client.js` is set to
`http://localhost:8081` to target the mock ESP32 server.

---

## 11. Phase 8 - Operations

- `scripts/setup-monitor-mode.sh` - sets Panda PAU0B to monitor mode on channel 6
- `docs/internal/HARDWARE_BRINGUP.md` - step-by-step flash + connect + verify runbook
- `reports/template.md` - session log template for lab exercises
- `.env.example` - environment variable defaults

---

## 12. Phase 9 - Acceptance

Final verification:

```bash
# Python side
pytest tests/ -v                         # 56 tests

# C++ side
ctest --test-dir src/ethical_validator/build --output-on-failure  # 2 test binaries

# Firmware
arduino-cli compile --fqbn esp32:esp32:esp32 src/attacker         # compile-only

# Helper collision check
scripts/check-cpp-helpers.sh

# E2E demo
scripts/demo-uc12.sh                     # all 4 alert types confirmed
```

The acceptance test `tests/test_acceptance_chain.py` runs the full server pipeline
against `chain.pcap` and asserts that all four alert types reach the broadcast
layer within 3 seconds.

---

## 13. Key Design Decisions

**Why offline-first?** Hardware is shared lab equipment. All logic must be verifiable
on any developer laptop before touching the device.

**Why synthetic PCAPs instead of real captures?** Reproducibility. The generator
uses a seeded RNG, so the same frames appear in the same order every run.

**Why a bounded queue with oldest-drop?** During beacon flood (50 frames/sec),
3000 frames arrive in 60 seconds. A 2048-slot queue absorbs all of them with margin.
The drop policy ensures the most recent alerts are always deliverable to the panel,
which matters more than preserving old ones.

**Why copy ethical_validator into the sketch root?** `arduino-cli` compiles only
the sketch root directory. A symlink would work on Linux but not on Windows Arduino
IDE, so a copy was chosen for portability.

**Why no authentication on the ESP32 API?** The API is only accessible on
`WARDEN_CONTROL` (192.168.4.x), a WPA2-PSK network with a known password. The
attack target network is never routed to this subnet. Per ADR-07.

**Why CANONICAL_API.md before code?** The LaTeX deliverable contained two
conflicting variants for several endpoint schemas. Writing a single authoritative
contract first prevented each subsystem from implementing a different variant.

---

## 14. Commit History Summary

63 commits from initial documentation to full system:

| Range | Content |
|---|---|
| d361c8b - c3f3ab9 | Initial documentation and project structure |
| dd14ffe - 76f9c29 | Phase 0: internal contracts, scaffolding, Python tooling |
| e50c47a - 1eb433a | Phase 1: Python detector (TDD, all analyzers + pipeline) |
| 8c02505 - 178eeee | Phase 1.5: Ethical Validator C++ library |
| 6937647 - 3eca373 | Phase 2: PCAP fixtures |
| 01f6d2a - a37e0b9 | Phase 3: Defender Panel (FastAPI + WebSocket + UI) |
| a4603b9 - 7fbb258 | Phase 4: ESP32 firmware foundation |
| ec846a0 - 93a492d | Phase 5: ESP32 REST API + OUI lookup |
| f8d64ad - ed3867b | Phase 6: Attack modules + frame builder + chain controller |
| 4dafc9b | Phase 7: Attacker Panel SPA |
| 5dab920 - 1142854 | Phase 8: Operations tooling |
| 117bbb5 - 709f178 | Phase 9: Acceptance tests + traceability |
