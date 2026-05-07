#include "config.h"
#include "ethical_validator.h"
#include <string.h>
#include <stdio.h>

WardenConfig g_config;

void config_init() {
    memset(&g_config, 0, sizeof(g_config));
    g_config.canal = EVIL_TWIN_CHANNEL_DEFAULT;
    g_config.duracion_beacon = DEFAULT_BEACON_DURATION;
    g_config.duracion_deauth = DEFAULT_DEAUTH_DURATION;
    g_config.duracion_evil_twin = DEFAULT_EVIL_TWIN_DURATION;
    g_config.beacons_por_segundo = DEFAULT_BEACONS_PER_SEC;
    g_config.bssid_validado = false;
    g_config.confirm_provided = false;
}

static bool parse_bssid(const char* str, uint8_t out[6]) {
    if (strlen(str) != 17) return false;
    for (int i = 0; i < 6; i++) {
        char byte_str[3] = {str[i*3], str[i*3+1], '\0'};
        char* end;
        long val = strtol(byte_str, &end, 16);
        if (*end != '\0') return false;
        out[i] = (uint8_t)val;
    }
    return true;
}

static const uint8_t ISP_OUI_BLACKLIST[][3] = {
    {0x10,0x05,0xCA}, {0xC4,0x6E,0x1F},  // Tigo
    {0x00,0x26,0x2D}, {0xE8,0xBE,0x81},  // Claro
    {0x5C,0x96,0x9D}, {0x00,0x24,0xD4},  // Movistar
    {0xA8,0x5A,0xF3},                    // ETB
};

bool config_set_bssid(const char* bssid_str, bool confirm) {
    uint8_t tmp[6];
    if (!parse_bssid(bssid_str, tmp)) return false;
    memcpy(g_config.bssid_bytes, tmp, 6);
    strncpy(g_config.bssid_objetivo, bssid_str, sizeof(g_config.bssid_objetivo) - 1);

    warden::ValidatorConfig vcfg{};
    vcfg.isp_oui_blacklist = ISP_OUI_BLACKLIST;
    vcfg.isp_oui_blacklist_count = sizeof(ISP_OUI_BLACKLIST) / sizeof(ISP_OUI_BLACKLIST[0]);

    auto result = warden::validate_bssid(g_config.bssid_bytes, confirm, vcfg);
    g_config.bssid_validado = (result == warden::ValidationResult::VALID);
    g_config.confirm_provided = confirm;
    return g_config.bssid_validado;
}

bool config_set_ssid(const char* ssid) {
    strncpy(g_config.ssid_clonar, ssid, sizeof(g_config.ssid_clonar) - 1);
    return true;
}

bool config_set_victima(const char* mac_str) {
    uint8_t tmp[6];
    if (!parse_bssid(mac_str, tmp)) return false;
    memcpy(g_config.mac_victima_bytes, tmp, 6);
    strncpy(g_config.mac_victima, mac_str, sizeof(g_config.mac_victima) - 1);
    g_config.mac_victima_set = true;
    return true;
}

void config_set_channel(uint8_t ch) {
    if (ch >= 1 && ch <= 13) g_config.canal = ch;
}
