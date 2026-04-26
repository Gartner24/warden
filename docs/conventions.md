# Conventions

Source: `deliverables/warden-design.tex` lines 111-195, `deliverables/warden-architecture.tex`, `deliverables/warden-use-cases.tex`

## WardenConfig fields (ESP32)

| Field | Default | Description |
|---|---|---|
| `bssid_objetivo` | - | Target AP MAC address (set before any attack) |
| `ssid_objetivo` | - | Target AP SSID |
| `canal` | 6 | WiFi channel for the attack |
| `duracion_beacon_flood` | 30 s | Phase 1 duration |
| `duracion_deauth` | 15 s | Phase 2 duration |
| `duracion_evil_twin` | 120 s | Phase 3 duration |
| `beacons_por_segundo` | 50 | Beacon emission rate |
| `prefijo_ssid_falso` | `"FakeNet"` | Prefix used to generate fake SSIDs in phase 1 |
| `bssid_validado` | false | Set to true by the Ethical Validator after `confirm` |

## Detector CLI arguments

| Argument | Description |
|---|---|
| `--iface <name>` | Monitor-mode interface (default: `panda0`) |
| `--channel <n>` | Lock interface to channel before capture |
| `--bssid <MAC>` | Protected BSSID to monitor |
| `--ssid <name>` | Protected SSID name |
| `--pcap <file>` | Offline PCAP mode; mutually exclusive with `--iface` |
| `--port <n>` | Override Defender Panel port (default: 8000) |

## Network addresses

| Network | Range | Owner |
|---|---|---|
| WARDEN_CONTROL AP | `192.168.4.0/24` | ESP32 control access point |
| Evil Twin AP (attack) | `10.0.0.0/24` | ESP32 rogue access point |
| Defender Panel | `127.0.0.1:8000` | FastAPI server (loopback only by default) |

## WARDEN_CONTROL AP

| Parameter | Value |
|---|---|
| SSID | `WARDEN_CONTROL` |
| Security | WPA2-PSK |
| Password | `warden-control-pwd` |
| Channel | 1 |
| Gateway | `192.168.4.1` |
| DHCP range | `192.168.4.10 - 192.168.4.50` |

The `WARDEN_CONTROL` AP runs on channel 1 while the lab router runs on channel 6 to keep the management/control radio path on a different non-overlapping channel from the attack radio path. This avoids contention when the ESP32 transmits attack frames on the lab channel and reduces the chance that the operator's panel session interferes with the attack itself.

## Naming rules

- Source files: `snake_case` for Python; `camelCase` for Arduino/C++.
- REST paths: `kebab-case` (e.g., `/oui-lookup`).
- Session report filenames: `session-YYYY-MM-DD.md` under `reports/`.
- PCAP filenames: descriptive, e.g., `chain-2025-04-25.pcap`, stored under `captures/`.

## Ethical Validator - blocked OUI prefixes

`LISTA_NEGRA_OUI_ISP` is defined in the firmware. It contains OUI prefixes assigned to consumer ISP-distributed hardware that should never appear as a target in the lab. The list is populated at firmware compile time; values are not documented here to avoid accidental targeting.
