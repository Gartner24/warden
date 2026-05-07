#pragma once
#include <Arduino.h>

#define WARDEN_CONTROL_SSID       "WARDEN_CONTROL"
#define WARDEN_CONTROL_PASSWORD   "warden-control-pwd"
#define WARDEN_CONTROL_CHANNEL    1
#define WARDEN_CONTROL_IP         "192.168.4.1"

#define EVIL_TWIN_AP_IP           "10.0.0.1"
#define EVIL_TWIN_CHANNEL_DEFAULT 6

#define DEFAULT_BEACON_DURATION   30
#define DEFAULT_DEAUTH_DURATION   15
#define DEFAULT_EVIL_TWIN_DURATION 120
#define DEFAULT_BEACONS_PER_SEC   50
#define DEFAULT_SSID_PREFIX       "FakeNet"

struct WardenConfig {
    char    bssid_objetivo[18];
    uint8_t bssid_bytes[6];
    char    ssid_clonar[33];
    uint8_t canal;
    uint16_t duracion_beacon;
    uint16_t duracion_deauth;
    uint16_t duracion_evil_twin;
    uint8_t  beacons_por_segundo;
    bool     bssid_validado;
    bool     confirm_provided;
    char     mac_victima[18];
    uint8_t  mac_victima_bytes[6];
    bool     mac_victima_set;
};

extern WardenConfig g_config;

void config_init();
bool config_set_bssid(const char* bssid_str, bool confirm);
bool config_set_ssid(const char* ssid);
void config_set_channel(uint8_t ch);
bool config_set_victima(const char* mac_str);
