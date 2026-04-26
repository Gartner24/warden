# Module: Attacker Firmware

Source: `deliverables/warden-architecture.tex` lines 170-189, `deliverables/warden-design.tex`

Runtime: C++ / Arduino-ESP32 2.0+ / ESP-IDF 5.0+, flashed to ESP32-WROOM-32.

## Responsibilities

Implements the full offensive chain and exposes a REST API that the Attacker Panel consumes. All network activity is constrained by the Ethical Validator before any phase can start.

## Internal modules

| Module | Responsibility |
|---|---|
| Controlador de Cadena | Drives the idle -> f1 -> f2 -> f3 -> finalizado state machine |
| Modulo Beacon Flood | Emits fake beacon frames at configurable rate (default 50/s) |
| Modulo Deauth | Emits deauthentication frames targeting the victim BSSID |
| Modulo Evil Twin | Configures the rogue AP; coordinates portal, DNS, and DHCP |
| Portal Cautivo | Serves the captive portal HTML; accepts and logs credential POST |
| Servidor DNS local | Answers all DNS queries with `10.0.0.1` |
| Servidor DHCP | Assigns addresses from `10.0.0.10-10.0.0.50` |
| Reconocedor | Active scan + passive client capture; populates the network list |
| Lookup OUI | Resolves MAC prefix to manufacturer via flash-embedded DB (~5 000 entries) |
| Configuracion | Holds the `WardenConfig` struct; accepts runtime updates via REST |
| Validador Etico | Verifies target BSSID is not OUI-blocked and operator has typed `confirm` |
| Interfaz Serial | Accepts operator commands over UART; emits status logs at 115200 baud |
| AP de Control | Runs `WARDEN_CONTROL` WPA2-PSK AP (192.168.4.1) for panel access |
| Servidor API REST | Exposes `/scan`, `/clients`, `/oui-lookup`, `/attack/*`, `/config`, `/credentials`, `/events` |

## Source layout (planned)

```
src/attacker/
|-- modules/
|   |-- beacon_flood/
|   |-- deauth/
|   |-- evil_twin/
|   |-- captive_portal/
|   |-- dns_server/
|   `-- dhcp_server/
`-- api/
    |-- api_server/
    |-- control_ap/
    |-- recon/
    `-- oui_lookup/
```

## REST API

See [`../api/esp32-rest.md`](../api/esp32-rest.md).
