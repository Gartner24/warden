#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

void recon_scan(JsonDocument& out);
void recon_clients(const uint8_t bssid[6], uint32_t duration_ms, JsonDocument& out);
