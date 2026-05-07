#include "beacon_flood.h"
#include "config.h"
#include "chain_controller.h"
#include "frame_builder.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_wifi.h>
#include <esp_random.h>

static TaskHandle_t _beacon_task = nullptr;

static void beacon_task(void* pvParam) {
    uint8_t buf[256];
    uint32_t delay_ms = 1000 / g_config.beacons_por_segundo;
    unsigned long last_log = 0;
    while (is_phase_active(EstadoCadena::FASE_1_BEACON)) {
        uint8_t bssid[6];
        esp_fill_random(bssid, 6);
        bssid[0] &= 0xFE;
        char ssid[32];
        snprintf(ssid, sizeof(ssid), "%s_%02X", DEFAULT_SSID_PREFIX, bssid[5]);
        size_t len = build_beacon_frame(buf, sizeof(buf), bssid, ssid, g_config.canal);
        if (len > 0) {
            esp_wifi_80211_tx(WIFI_IF_AP, buf, len, false);
            g_chain_state.beacons_emitidos++;
        }
        if (millis() - last_log >= 1000) {
            Serial.printf("[FASE_1] beacons=%lu ch=%d\n",
                          (unsigned long)g_chain_state.beacons_emitidos, g_config.canal);
            last_log = millis();
        }
        vTaskDelay(pdMS_TO_TICKS(delay_ms));
    }
    _beacon_task = nullptr;
    vTaskDelete(nullptr);
}

void beacon_flood_task_start() {
    if (_beacon_task) return;
    xTaskCreatePinnedToCore(beacon_task, "beacon_emitter", 4096, nullptr,
                            tskIDLE_PRIORITY + 4, &_beacon_task, 1);
}

void beacon_flood_task_stop() {
    // Task self-deletes when phase ends; just clear handle
    _beacon_task = nullptr;
}
