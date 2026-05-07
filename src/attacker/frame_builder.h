#pragma once
#include <stdint.h>
#include <stddef.h>

size_t build_beacon_frame(uint8_t* out, size_t cap,
                          const uint8_t bssid[6], const char* ssid, uint8_t channel);
size_t build_deauth_frame(uint8_t* out, size_t cap,
                          const uint8_t target[6], const uint8_t bssid[6], uint16_t reason);
