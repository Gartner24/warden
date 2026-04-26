# Threat Model

Source: `deliverables/warden-threat-model.tex` (full document)

## Attack phases and detection objectives

| Phase | MITRE ATT&CK | Detection ID | Heuristic |
|---|---|---|---|
| Beacon Flood | T1498 | D-01 | Anomalous unique-beacons-per-second rate |
| Deauthentication | T1499 | D-02 | Deauth frame count to protected BSSID in time window |
| Evil Twin | T1557 + T1056.003 | D-03 | Duplicate SSID with BSSID different from the protected one |
| Full chain (correlation) | - | D-07 | Temporal correlation of D-01 + D-02 + D-03 |

## Lab threat actors

| Actor | Role |
|---|---|
| Operador del Atacante | Operates the ESP32 chain via the Attacker Panel; authorized lab personnel |
| Operador del Detector | Operates the Python detector and Defender Panel; authorized lab personnel |
| Operador de la Victima | Connects to the Evil Twin; demonstrates credential capture (UC-11) |

## Lab environment

- Router: `LAB_WARDEN_UTP`, channel 6, WPA2
- Primary victim: Redmi Note 7 (MIUI 12.5)
- Secondary victim: Dell Latitude E6220 (Ubuntu Server 22.04.5 LTS)
- Demo credentials used in lab runs: `demo.user@warden.test` / `demo-password-12345`

## Ethical constraints

All attacks are restricted to the lab environment by the in-firmware Ethical Validator (ADR-06). See [`modules/ethical-validator.md`](modules/ethical-validator.md).

For the full threat model analysis, risk assessment, and STRIDE breakdown see `deliverables/warden-threat-model.tex`.
