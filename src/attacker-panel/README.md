# Attacker Panel (Static SPA)

Vanilla JS + Tailwind CDN frontend. Served from operator laptop, talks to ESP32 over HTTP.

## Dev mode (offline)
```bash
cd src/attacker-panel
python3 -m http.server 8080
# Then start mock ESP32: uvicorn tools.mock-esp32.server:app --port 8081
```

## References
- API contract: docs/internal/CANONICAL_API.md
- Module details: docs/modules/attacker-panel.md
