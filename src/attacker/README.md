# Attacker Firmware (ESP32)

Arduino sketch for the WARDEN offensive chain (Beacon Flood -> Deauth -> Evil Twin).

## Required Arduino Libraries
- ESPAsyncWebServer
- AsyncTCP
- ArduinoJson 7.0+

## References
- Architecture: docs/architecture.md
- Module details: docs/modules/attacker-firmware.md
- API contract: docs/internal/CANONICAL_API.md
- Constants: docs/internal/CONSTANTS.md
- FreeRTOS task model: docs/internal/FIRMWARE_RUNTIME.md
