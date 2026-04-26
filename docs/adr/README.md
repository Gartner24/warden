# Architectural Decision Records

Source: `deliverables/warden-architecture.tex` lines 794-1132

One file per decision. All ADRs are **Accepted** (recorded post-decision from the formal SAD).

## Index

| ADR | Title | Key trade-off |
|---|---|---|
| [0001](0001-air-only-comms.md) | Air-only inter-subsystem comms | Realism over convenience |
| [0002](0002-python-scapy-detector.md) | Python + Scapy for the detector | Ecosystem richness over raw performance |
| [0003](0003-esp32-offensive.md) | ESP32 for the offensive subsystem | Cost and WiFi stack over general compute |
| [0004](0004-no-ml-heuristics.md) | Heuristic detection, no ML | Explainability over adaptability |
| [0005](0005-external-config.md) | External configuration | Flexibility over hardcoding |
| [0006](0006-ethical-validator-in-firmware.md) | Ethical Validator in firmware | Tamper-resistance over UI simplicity |
| [0007](0007-hybrid-attacker-panel.md) | Hybrid Attacker Panel (off-device) | Unrestricted JS over flash constraints |
| [0008](0008-fastapi-websockets.md) | FastAPI + WebSockets for Defender Panel | Real-time push over polling |
| [0009](0009-oui-flash-embedded.md) | OUI DB embedded in ESP32 flash | Offline capability over freshness |

## Template

```markdown
# ADR-NNNN: <title>
- Status: Accepted
- Date: YYYY-MM-DD
- Source: deliverables/warden-architecture.tex:<line>

## Context
## Decision
## Consequences
```
