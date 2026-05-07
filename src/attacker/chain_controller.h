#pragma once
#include <Arduino.h>

enum class EstadoCadena : uint8_t {
    IDLE,
    FASE_1_BEACON,
    FASE_2_DEAUTH,
    FASE_3_EVIL,
    FINALIZADO,
    ERROR_ESTADO
};

struct EstadoCadenaInfo {
    EstadoCadena estado;
    unsigned long fase_inicio_ms;
    unsigned long uptime_ms;
    uint32_t beacons_emitidos;
    uint32_t deauths_emitidos;
    uint32_t clientes_evil_twin;
    uint32_t credenciales_capturadas;
    bool ataque_activo;
};

extern EstadoCadenaInfo g_chain_state;

void chain_controller_init();
void chain_controller_start(const char* modo);
void chain_controller_stop();
bool is_phase_active(EstadoCadena fase);
const char* estado_to_string(EstadoCadena e);
