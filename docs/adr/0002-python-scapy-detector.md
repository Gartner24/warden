# ADR-0002: Python + Scapy for the defensive subsystem

- Status: Accepted
- Source: `deliverables/warden-architecture.tex:837`

## Context

The detector needs to capture and parse 802.11 management frames, implement sliding-window counters, and serve a real-time web dashboard - all in an academic timeline.

## Decision

Use Python 3.10+ with Scapy 2.5+ for frame capture and parsing, and FastAPI 0.110+ with Uvicorn 0.27+ for the web layer.

## Consequences

- Rich ecosystem (Scapy, asyncio, FastAPI) shortens development time.
- Python is slower than C or Go, but sub-second latency is not required for the academic detection scenario.
- The team is already proficient in Python, reducing ramp-up cost.
