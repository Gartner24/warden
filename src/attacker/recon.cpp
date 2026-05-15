#include "recon.h"
#include "config.h"
#include "oui_lookup.h"
#include <string.h>
#include <esp_wifi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>

ReconScanState g_recon_state = RECON_IDLE;

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

// --- Async client discovery ---

struct ClientEntry { uint8_t mac[6]; uint16_t frames; };
static ClientEntry _clients[32];
static int _client_count = 0;
static uint8_t _sniff_bssid[6];
static uint8_t _sniff_canal = 6;

static bool _mac_is_multicast(const uint8_t* m) { return (m[0] & 0x01) != 0; }
static bool _mac_eq(const uint8_t* a, const uint8_t* b) { return memcmp(a, b, 6) == 0; }

static void _record_client(const uint8_t* mac) {
    if (_mac_is_multicast(mac)) return;
    for (int i = 0; i < _client_count; i++) {
        if (_mac_eq(_clients[i].mac, mac)) { _clients[i].frames++; return; }
    }
    if (_client_count < 32) {
        memcpy(_clients[_client_count].mac, mac, 6);
        _clients[_client_count].frames = 1;
        _client_count++;
    }
}

static void _promisc_cb(void* buf, wifi_promiscuous_pkt_type_t type) {
    if (type == WIFI_PKT_MISC) return;
    const wifi_promiscuous_pkt_t* p = (const wifi_promiscuous_pkt_t*)buf;
    if (p->rx_ctrl.sig_len < 24) return;

    const uint8_t fc0 = p->payload[0];
    const uint8_t fc1 = p->payload[1];
    const uint8_t frame_type = (fc0 >> 2) & 0x03; // 0=mgmt, 2=data
    const uint8_t* addr1 = p->payload + 4;
    const uint8_t* addr2 = p->payload + 10;
    const uint8_t* addr3 = p->payload + 16;

    if (frame_type == 0) {
        uint8_t subtype = (fc0 >> 4) & 0x0F;
        // Probe request (subtype 4): addr2 = requesting client, addr1/addr3 = broadcast
        if (subtype == 4) {
            _record_client(addr2);
            return;
        }
        // For all other management frames, filter by BSSID
        if (!_mac_eq(addr3, _sniff_bssid)) return;
        if (!_mac_eq(addr2, _sniff_bssid)) _record_client(addr2);
        if (!_mac_eq(addr1, _sniff_bssid)) _record_client(addr1);
    } else if (frame_type == 2) {
        // Data frames: use ToDS/FromDS bits
        bool toDS   = (fc1 >> 0) & 0x01;
        bool fromDS = (fc1 >> 1) & 0x01;
        if (toDS && !fromDS) {
            // client → AP: addr1=BSSID, addr2=client
            if (_mac_eq(addr1, _sniff_bssid)) _record_client(addr2);
        } else if (!toDS && fromDS) {
            // AP → client: addr1=client, addr2=BSSID
            if (_mac_eq(addr2, _sniff_bssid)) _record_client(addr1);
        }
    }
}

static void _scan_task(void* pvParam) {
    _client_count = 0;
    memset(_clients, 0, sizeof(_clients));

    esp_wifi_set_promiscuous_rx_cb(_promisc_cb);
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_channel(_sniff_canal, WIFI_SECOND_CHAN_NONE);

    while (g_recon_state == RECON_RUNNING) {
        vTaskDelay(pdMS_TO_TICKS(200));
    }

    esp_wifi_set_promiscuous(false);
    esp_wifi_set_promiscuous_rx_cb(nullptr);
    esp_wifi_set_channel(WARDEN_CONTROL_CHANNEL, WIFI_SECOND_CHAN_NONE);

    g_recon_state = RECON_DONE;
    vTaskDelete(nullptr);
}

void recon_clients_start(const uint8_t bssid[6], uint8_t canal) {
    if (g_recon_state == RECON_RUNNING) {
        if (_mac_eq(_sniff_bssid, bssid)) return;
        g_recon_state = RECON_IDLE;
        vTaskDelay(pdMS_TO_TICKS(250));
    }
    memcpy(_sniff_bssid, bssid, 6);
    _sniff_canal = canal;
    g_recon_state = RECON_RUNNING;
    xTaskCreatePinnedToCore(_scan_task, "client_scan", 4096, nullptr,
                            tskIDLE_PRIORITY + 2, nullptr, 0);
}

void recon_clients_fill(JsonDocument& out) {
    out["ok"] = true;
    out["scanning"] = (g_recon_state == RECON_RUNNING);
    out["clientes_detectados"] = _client_count;
    JsonArray arr = out["clientes"].to<JsonArray>();
    for (int i = 0; i < _client_count; i++) {
        char mac_str[18];
        snprintf(mac_str, sizeof(mac_str), "%02X:%02X:%02X:%02X:%02X:%02X",
                 _clients[i].mac[0], _clients[i].mac[1], _clients[i].mac[2],
                 _clients[i].mac[3], _clients[i].mac[4], _clients[i].mac[5]);
        JsonObject c = arr.add<JsonObject>();
        c["mac"] = mac_str;
        c["frames_observados"] = _clients[i].frames;
    }
    if (g_recon_state == RECON_DONE) g_recon_state = RECON_IDLE;
}
