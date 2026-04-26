# ADR-0007: Hybrid Attacker Panel (frontend served off-device)

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:978`

## Context

The Attacker Panel needs a rich, interactive UI. Serving it from the ESP32 flash would compete with the OUI database and firmware for the 4 MB budget, and would limit JS size and update frequency.

## Decision

The Attacker Panel HTML/JS is served from the operator's laptop (via `python3 -m http.server` or as a local file). The ESP32 only serves JSON from its REST API.

## Consequences

- No flash budget pressure for the frontend.
- Frontend can be updated without reflashing the ESP32.
- Operator laptop must be joined to `WARDEN_CONTROL` for the panel's fetch calls to reach `192.168.4.1`.
- CORS: the ESP32 API must allow requests from `localhost` or `file://` origins.
