# Module: Attacker Panel

Source: `deliverables/warden-architecture.tex` lines 526, 595-601, 659-667

Runtime: Static HTML + vanilla JS + Tailwind CSS via CDN. No build step. Served from the operator laptop via `python3 -m http.server` or opened as `file:///`.

## Responsibilities

Browser UI for the attack operator. Connects to the ESP32 REST API at `192.168.4.1:80` (operator laptop must be joined to `WARDEN_CONTROL`). Provides network scanning, target selection, ethical confirmation, phase control, and credential review.

## Source layout (planned)

```
src/attacker-panel/
|-- index.html
`-- assets/
    |-- styles.css
    `-- app.js
```

## Key interactions

- `GET /scan` -> display discovered networks
- `GET /clients` -> display associated clients with OUI-resolved manufacturer
- `POST /config` -> set target BSSID, SSID, channel, phase durations
- `POST /attack/start` -> trigger full chain (requires `confirm` from Validador Etico)
- `POST /attack/stop` -> abort current phase
- `GET /credentials` -> show captured credentials from captive portal
- `GET /events` (SSE or polling) -> live status updates

## Notes

- ADR-07: the panel runs off the operator's laptop, not off the ESP32 flash. This avoids 4 MB flash constraints and allows arbitrary JS complexity.
- The ESP32 only serves JSON; the HTML/JS frontend is fully decoupled.
