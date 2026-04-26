# ADR-0003: ESP32 for the offensive subsystem

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:872`

## Context

The offensive subsystem must emit raw 802.11 management frames (beacons, deauth, probe responses) and run a rogue AP with DHCP and DNS simultaneously. The hardware budget is ~30 USD.

## Decision

Use an ESP32-WROOM-32 (4 MB flash, 520 KB RAM) with the Arduino-ESP32 2.0+ / ESP-IDF 5.0+ stack.

## Consequences

- ESP32 natively supports raw 802.11 frame injection and concurrent SoftAP + Station modes.
- FreeRTOS multitasking allows beacon flood, deauth, DNS, and DHCP to run as parallel tasks.
- 4 MB flash is enough for the OUI database (~5 000 entries) and all firmware modules.
- Limited RAM (520 KB) caps the in-memory credential store; credentials are volatile and lost on reset.
