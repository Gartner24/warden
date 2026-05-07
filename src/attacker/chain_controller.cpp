#include "chain_controller.h"
#include <string.h>

EstadoCadenaInfo g_chain_state;

void chain_controller_init() {
    memset(&g_chain_state, 0, sizeof(g_chain_state));
    g_chain_state.estado = EstadoCadena::IDLE;
}

void chain_controller_start(const char* modo) {
    g_chain_state.ataque_activo = true;
    g_chain_state.estado = EstadoCadena::FASE_1_BEACON;
    g_chain_state.fase_inicio_ms = millis();
}

void chain_controller_stop() {
    g_chain_state.ataque_activo = false;
    g_chain_state.estado = EstadoCadena::IDLE;
}

bool is_phase_active(EstadoCadena fase) {
    return g_chain_state.estado == fase;
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
