#include "evil_twin.h"
#include "config.h"
#include "chain_controller.h"
#include "control_ap.h"
#include <WiFi.h>
#include <Arduino.h>

void evil_twin_start() {
    control_ap_stop();
    delay(100);
    IPAddress ap_ip(10, 0, 0, 1);
    IPAddress gateway(10, 0, 0, 1);
    IPAddress subnet(255, 255, 255, 0);
    WiFi.softAPConfig(ap_ip, gateway, subnet);
    WiFi.softAP(g_config.ssid_clonar, "", g_config.canal);
    Serial.printf("[INFO] [%lu] Evil Twin AP started: SSID=%s ch=%d\n",
                  millis(), g_config.ssid_clonar, g_config.canal);
}

void evil_twin_stop() {
    WiFi.softAPdisconnect(true);
    delay(100);
    control_ap_start();
}
