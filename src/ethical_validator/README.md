# Ethical Validator (C++ host-buildable library)

Validates target BSSID against a blacklist before authorizing any attack. Compiled on host via CMake for unit tests; included in ESP32 sketch for runtime enforcement.

## Build and test (host, no hardware required)
```bash
cmake -S src/ethical_validator -B src/ethical_validator/build
cmake --build src/ethical_validator/build
ctest --test-dir src/ethical_validator/build --output-on-failure
```

## References
- Module details: docs/modules/ethical-validator.md
- API contract: docs/internal/CANONICAL_API.md
