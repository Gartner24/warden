# ADR-0009: OUI database embedded in ESP32 flash

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:1086`

## Context

The Reconocedor and Ethical Validator need to resolve MAC prefixes to manufacturer names and check OUI blocks without internet access (the lab router has no internet).

## Decision

A curated OUI lookup table of ~5 000 entries is compiled into the ESP32 firmware and stored in flash. It is queried at runtime without any network call.

## Consequences

- Works fully offline in the air-gapped lab environment.
- The database is static at flash time; entries added to the IEEE OUI registry after the last firmware build will not be resolved.
- The ~5 000 entry table fits comfortably within the 4 MB flash budget alongside all other firmware modules.
- Updating the OUI database requires reflashing the ESP32.
