# ADR-0001: Air-only inter-subsystem communication

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:802`

## Context

The offensive (ESP32) and defensive (Python detector) subsystems need to be independent enough to be deployed separately or used in different exercises.

## Decision

All communication between the two subsystems happens exclusively via the 802.11 air interface. There is no direct socket, serial line, shared file, or any digital out-of-band channel between them.

## Consequences

- The detector observes the same frames a real WIDS would see - no artificial injection.
- The two subsystems can be physically separated (different rooms, different operators).
- Adding a shared control channel (e.g., to sync timing) would require a protocol over WiFi, not a direct link.
