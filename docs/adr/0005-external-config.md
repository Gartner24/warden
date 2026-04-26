# ADR-0005: External (out-of-code) configuration

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:931`

## Context

Lab parameters (target BSSID, channel, attack durations, detection thresholds) change between sessions. Hardcoding them would require reflashing the ESP32 or redeploying the detector for each session.

## Decision

All session parameters are supplied at runtime - via the REST API for the ESP32 and via CLI arguments for the detector. No session-specific values are hardcoded in source files.

## Consequences

- Session setup is faster: change the target BSSID in the panel, not in the code.
- The `WardenConfig` struct on the ESP32 and the CLI argument parser on the detector are the single configuration surfaces. See [`../conventions.md`](../conventions.md) for the full field list.
- Secrets (passwords, OUI blocklists) must not be committed to the repo; use `.env` files or pass them at runtime.
