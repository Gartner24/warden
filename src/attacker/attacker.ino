#include "config.h"

void setup() {
    Serial.begin(115200);
    config_init();
}

void loop() {
    delay(1000);
}
