#include "config.h"
#include "serial_interface.h"
#include "control_ap.h"
#include "api_server.h"
#include "chain_controller.h"

void setup() {
    Serial.begin(115200);
    config_init();
    chain_controller_init();
    serial_interface_init();
    control_ap_start();
    api_server_start();
    Serial.println("[INFO] [0] WARDEN ready");
}

void loop() {
    serial_interface_tick();
    delay(10);
}
