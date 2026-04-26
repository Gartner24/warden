# ADR-0006: Ethical Validator inside the firmware

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:953`

## Context

WARDEN must enforce that attacks only target lab-owned hardware. A UI-only check (in the Attacker Panel JS) can be bypassed with a direct HTTP call to the ESP32 API.

## Decision

The Ethical Validator lives inside the ESP32 firmware. It runs synchronously before any attack phase. It cannot be bypassed without reflashing the device. See [`ethical-validator.md`](ethical-validator.md) for validation rules.

## Consequences

- The protection is tamper-resistant under normal lab conditions.
- Adds a firmware dependency on the OUI blocklist and the `confirm` keyword check.
- Operators cannot start an attack accidentally or via an automated script without explicitly passing the confirmation.
