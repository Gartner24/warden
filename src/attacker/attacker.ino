#include "config.h"
#include "serial_interface.h"
#include "api_server.h"
#include "control_ap.h"
#include "chain_controller.h"
#include <Arduino.h>

#define BUTTON_PIN 0  // GPIO 0 (BOOT button on most ESP32 devkits)

static volatile bool _btn_pressed = false;

static void IRAM_ATTR btn_isr() {
    _btn_pressed = true;
}

void setup() {
    Serial.begin(115200);
    config_init();
    chain_controller_init();
    serial_interface_init();
    control_ap_start();
    api_server_start();
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), btn_isr, FALLING);
    Serial.println("[INFO] [0] WARDEN ready");
}

void loop() {
    serial_interface_tick();
    if (_btn_pressed) {
        _btn_pressed = false;
        if (!g_chain_state.ataque_activo && g_config.bssid_validado) {
            chain_controller_start("cadena_automatica");
        }
    }
    delay(10);
}
