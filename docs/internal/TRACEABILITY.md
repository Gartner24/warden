# Requirement Traceability Matrix

## Summary

- Alta-priority: 12 implemented, 10 tested
- Media-priority: 5 implemented, 3 tested
- Baja-priority: 1 implemented, 1 tested

| Requirement ID | Description | Priority | Implemented In | Tested In | Status |
|---|---|---|---|---|---|
| RF-OFF-001 | Beacon flood attack | Alta | src/attacker/beacon_flood.cpp | - (hardware) | IMPL |
| RF-OFF-002 | Deauth attack | Alta | src/attacker/deauth_module.cpp | - (hardware) | IMPL |
| RF-OFF-003 | Evil Twin attack | Alta | src/attacker/evil_twin.cpp | - (hardware) | IMPL |
| RF-OFF-004 | 3-phase chain attack | Alta | src/attacker/chain_controller.cpp | - (hardware) | IMPL |
| RF-PAT-001 | Beacon flood detection | Alta | src/detector/analyzers/beacon_flood.py | tests/detector/analyzers/test_beacon_flood.py | TESTED |
| RF-PAT-002 | Deauth detection | Alta | src/detector/analyzers/deauth.py | tests/detector/analyzers/test_deauth.py | TESTED |
| RF-PAT-003 | Evil Twin detection | Alta | src/detector/analyzers/evil_twin.py | tests/detector/analyzers/test_evil_twin.py | TESTED |
| RF-PAT-004 | Chain correlation | Alta | src/detector/correlator.py | tests/detector/test_correlator.py | TESTED |
| RF-DEF-001 | WebSocket alert delivery | Alta | src/detector/web/server.py | tests/detector/web/test_server_integration.py | TESTED |
| RF-DEF-002 | Defender Panel UI | Media | src/detector/web/static/ | - (manual) | IMPL |
| RF-DEF-003 | Session reset | Media | src/detector/web/routes.py | tests/detector/web/test_routes.py | TESTED |
| RF-PDE-001 | PCAP-based offline testing | Alta | src/detector/capture/pcap_capture.py | tests/detector/test_pcap_capture.py | TESTED |
| RF-PDE-002 | Live capture interface | Media | src/detector/capture/live_capture.py | tests/detector/test_live_capture_smoke.py | TESTED |
| RF-SYS-001 | Ethical validator gate | Alta | src/attacker/ethical_validator.cpp | src/ethical_validator/tests/test_validator.cpp | TESTED |
| RF-SYS-002 | ISP OUI blacklist | Alta | src/attacker/config.cpp | src/ethical_validator/tests/test_validator.cpp | TESTED |
| RF-SYS-003 | Operator confirmation | Alta | src/attacker-panel/assets/views/ethics.js | - (manual) | IMPL |
| RF-SYS-004 | Serial command interface | Media | src/attacker/serial_interface.cpp | - | IMPL |
| RF-SYS-005 | Session reporting | Baja | src/detector/session.py | tests/detector/test_session.py | TESTED |
