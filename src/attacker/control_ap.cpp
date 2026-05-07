#include "control_ap.h"
#include "config.h"
#include <Arduino.h>

static bool _ap_running = false;

void control_ap_start() {
    IPAddress local_ip(192, 168, 4, 1);
    IPAddress gateway(192, 168, 4, 1);
    IPAddress subnet(255, 255, 255, 0);
    WiFi.softAPConfig(local_ip, gateway, subnet);
    WiFi.softAP(WARDEN_CONTROL_SSID, WARDEN_CONTROL_PASSWORD, WARDEN_CONTROL_CHANNEL);
    _ap_running = true;
    Serial.printf("[INFO] [%lu] Control AP started: SSID=%s ch=%d IP=%s\n",
                  millis(), WARDEN_CONTROL_SSID, WARDEN_CONTROL_CHANNEL, WARDEN_CONTROL_IP);
}

void control_ap_stop() {
    WiFi.softAPdisconnect(true);
    _ap_running = false;
}

bool control_ap_is_running() {
    return _ap_running;
}
