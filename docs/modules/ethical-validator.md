# Module: Ethical Validator

Source: `deliverables/warden-architecture.tex` line 188, `deliverables/warden-design.tex` lines 170-195 (ADR-06)

Runtime: C++, runs inside the ESP32 firmware.

## Responsibilities

Hard gate that prevents the offensive chain from targeting any network outside the authorized lab environment. Runs synchronously before any attack phase is allowed to start. Cannot be bypassed by the REST API.

## Validation rules (in order)

1. Target BSSID is not the broadcast address (`FF:FF:FF:FF:FF:FF`) and is not null.
2. Target BSSID OUI is not in `LISTA_NEGRA_OUI_ISP` (ISP-issued hardware that should never appear in a lab).
3. Operator has explicitly typed the keyword `confirm` in the confirmation field of the Attacker Panel.

If any rule fails the chain is blocked and an error is returned to the panel. No frames are emitted.

## Configuration

The allowlist/blacklist is an out-of-code configuration (ADR-05). See [`../conventions.md`](../conventions.md) for the `WardenConfig` fields involved (`bssid_validado`, `LISTA_NEGRA_OUI_ISP`).

## Notes

- ADR-06 justifies placing the Validator inside the firmware rather than only in the panel UI. A purely frontend check could be bypassed with a direct HTTP call; a firmware-side check cannot be bypassed without reflashing.
- The `confirm` keyword is intentionally not a checkbox - it requires deliberate keyboard input from the operator.
