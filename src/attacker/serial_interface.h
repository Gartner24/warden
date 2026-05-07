#pragma once
#include <Arduino.h>

enum class CommandType : uint8_t {
    HELP, STATUS, START, STOP, RESET, CREDENTIALS,
    SET_BSSID, SET_SSID, SET_CHANNEL, SET_DURATION,
    UNKNOWN
};

struct ParsedCommand {
    CommandType type;
    char        arg1[64];
    char        arg2[64];
    uint8_t     channel;
    uint16_t    duration;
    bool        confirm;
};

void serial_interface_init();
void serial_interface_tick();
bool parse_command(const String& line, ParsedCommand& out);
String format_log(const char* level, unsigned long ms, const char* msg);
