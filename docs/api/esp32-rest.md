# API: ESP32 REST

Source: `deliverables/warden-architecture.tex` line 184, `deliverables/warden-design.tex`

Base URL: `http://192.168.4.1` (operator laptop must be joined to `WARDEN_CONTROL`)

All request and response bodies are JSON. No authentication beyond being on the `WARDEN_CONTROL` SSID.

## Endpoints

### Recon

| Method | Path | Description |
|---|---|---|
| POST | `/scan` | Trigger active network scan; returns list of discovered BSSIDs |
| GET | `/clients` | List associated clients with MAC, OUI-resolved manufacturer, RSSI |
| GET | `/oui-lookup?mac=<MAC>` | Resolve a single MAC prefix to manufacturer name |

### Configuration

| Method | Path | Description |
|---|---|---|
| GET | `/config` | Read current `WardenConfig` fields |
| POST | `/config` | Update `WardenConfig` fields (BSSID, SSID, channel, durations, etc.) |

### Attack control

| Method | Path | Description |
|---|---|---|
| POST | `/attack/start` | Start the full automated chain (requires `confirm` field) |
| POST | `/attack/start/beacon` | Start Beacon Flood phase only |
| POST | `/attack/start/deauth` | Start Deauth phase only |
| POST | `/attack/start/eviltwin` | Start Evil Twin phase only |
| POST | `/attack/stop` | Abort the current phase and return to idle |

### Monitoring

| Method | Path | Description |
|---|---|---|
| GET | `/credentials` | Return credentials logged by the captive portal (volatile) |
| GET | `/events` | Server-Sent Events stream of status updates |

## Notes

- TBD: exact request/response schemas to be documented when firmware is implemented.
- The `/attack/start` endpoint checks the Ethical Validator before taking action. If validation fails, it returns `400` with a reason.
