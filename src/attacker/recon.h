#pragma once
#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFi.h>

enum ReconScanState { RECON_IDLE, RECON_RUNNING, RECON_DONE };
extern ReconScanState g_recon_state;

void recon_scan(JsonDocument& out);
void recon_clients_start(const uint8_t bssid[6], uint8_t canal);
void recon_clients_fill(JsonDocument& out);
