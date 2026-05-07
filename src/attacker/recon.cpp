#include "recon.h"
#include "oui_lookup.h"
#include <string.h>

void recon_scan(JsonDocument& out) {
    int n = WiFi.scanNetworks(false, true, false, 200);
    out["ok"] = true;
    JsonArray redes = out["redes"].to<JsonArray>();
    for (int i = 0; i < n; i++) {
        JsonObject red = redes.add<JsonObject>();
        red["ssid_objetivo"] = WiFi.SSID(i).c_str();
        red["bssid_objetivo"] = WiFi.BSSIDstr(i).c_str();
        red["rssi_dbm"] = WiFi.RSSI(i);
        red["canal"] = WiFi.channel(i);
        switch (WiFi.encryptionType(i)) {
            case WIFI_AUTH_OPEN:    red["cifrado"] = "OPEN"; break;
            case WIFI_AUTH_WEP:     red["cifrado"] = "WEP"; break;
            case WIFI_AUTH_WPA_PSK: red["cifrado"] = "WPA"; break;
            default:                red["cifrado"] = "WPA2"; break;
        }
        char vendor[32];
        const uint8_t* bssid = WiFi.BSSID(i);
        lookup_oui(bssid, vendor, sizeof(vendor));
        red["fabricante"] = vendor;
    }
    out["redes_encontradas"] = n;
    WiFi.scanDelete();
}

void recon_clients(const uint8_t bssid[6], uint32_t duration_ms, JsonDocument& out) {
    out["ok"] = true;
    out["clientes_detectados"] = 0;
    out["clientes"].to<JsonArray>();
}
