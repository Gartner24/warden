# WARDEN Constants Registry

> Every PR that adds or changes a constant MUST update this file.
> Every agent starting work on this codebase MUST read this file first.

This is the **single source of truth** for all numeric constants and configuration
values used across the WARDEN firmware, detector, and panels. Do not hardcode any
value that appears here without referencing this document.

---

## Channels

| Name              | Channel | Purpose                         |
|-------------------|---------|---------------------------------|
| `WARDEN_CONTROL`  | 1       | AP control network channel      |
| `LAB_WARDEN_UTP`  | 6       | Lab protected network channel   |
| `EVIL_TWIN`       | 6       | Matches target; monitor default |

---

## Networks

| Network          | SSID                  | Security        | AP IP        | DHCP Range                    | Lease | Notes                              |
|------------------|-----------------------|-----------------|--------------|-------------------------------|-------|------------------------------------|
| WARDEN_CONTROL   | `WARDEN_CONTROL`      | WPA2-PSK        | 192.168.4.1  | 192.168.4.10 - 192.168.4.50   | -     | Password: `warden-control-pwd`, ch1 |
| Evil Twin        | cloned from target    | OPEN (no auth)  | 10.0.0.1     | 10.0.0.10 - 10.0.0.50         | 12h   | DNS wildcard -> 10.0.0.1 TTL 60   |
| Defender Panel   | -                     | loopback only   | 127.0.0.1    | -                             | -     | Port 8000                          |
| Attacker Panel   | -                     | dev only        | localhost    | -                             | -     | Port 8080, `python3 -m http.server` |

---

## Timing Defaults (seconds)

| Constant                 | Value    | Description                                   |
|--------------------------|----------|-----------------------------------------------|
| `duracion_beacon_flood`  | 30       | Duration of beacon flood attack (s)           |
| `duracion_deauth`        | 15       | Duration of deauth attack (s)                 |
| `duracion_evil_twin`     | 120      | Duration of evil twin session (s)             |
| `beacons_por_segundo`    | 50       | Beacon frames emitted per second              |
| `prefijo_ssid_falso`     | `FakeNet`| SSID prefix for fake network identifiers      |
| `ventana_correlacion`    | 60       | Correlation window for event linking (s)      |

---

## Detector Thresholds (defaults)

| Constant                  | Value | Description                                        |
|---------------------------|-------|----------------------------------------------------|
| `umbral_beacons_por_seg`  | 30    | Beacon frames/sec above which alert is triggered   |
| `ventana_beacon_seg`      | 5     | Sliding window for beacon rate measurement (s)     |
| `umbral_deauth_por_seg`   | 5     | Deauth frames/sec above which alert is triggered   |
| `ventana_deauth_seg`      | 3     | Sliding window for deauth rate measurement (s)     |
| `cooldown_alerta_seg`     | 5     | Minimum interval between repeated alerts (s)       |

---

## OUI Test Fixtures

| OUI prefix | Vendor                | Status                                                                     |
|------------|-----------------------|----------------------------------------------------------------------------|
| `9C:EF:D5` | Panda Wireless, Inc.  | **LOCKED** - do not change; verified against IEEE OUI registry             |

---

## ISP-OUI Blacklist (Validador Etico)

Values are intentionally maintained in code, not duplicated here, to avoid
accidental targeting. See:
`src/ethical_validator/include/ethical_validator.h::LISTA_NEGRA_OUI_ISP`

The table below lists representative Colombian ISP OUIs as examples only.
**These are samples, not an exhaustive list.**

| ISP       | OUI samples          |
|-----------|----------------------|
| Tigo      | `10:05:CA`, `C4:6E:1F` |
| Claro     | `00:26:2D`, `E8:BE:81` |
| Movistar  | `5C:96:9D`, `00:24:D4` |
| ETB       | `A8:5A:F3`           |

---

## MITRE ATT&CK Mappings

| Technique ID        | Technique Name                              | WARDEN Phase       |
|---------------------|---------------------------------------------|--------------------|
| `T1498`             | Network Denial of Service                   | Beacon Flood       |
| `T1499`             | Endpoint Denial of Service                  | Deauth             |
| `T1557 + T1056.003` | Adversary-in-the-Middle + Web Portal Capture | Evil Twin          |

---

## Demo Credentials (lab only)

| Field    | Value                        |
|----------|------------------------------|
| User     | `demo.user@warden.test`      |
| Password | `demo-password-12345`        |

- TLD `.test` is reserved per RFC 2606 and will never resolve on the public internet.
- These credentials are for portal capture testing only.
- **Never use real credentials in this environment.**
