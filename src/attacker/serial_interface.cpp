#include "serial_interface.h"
#include "config.h"
#include <string.h>

String format_log(const char* level, unsigned long ms, const char* msg) {
    String s = "[";
    s += level;
    s += "] [";
    s += String(ms);
    s += "] ";
    s += msg;
    return s;
}

bool parse_command(const String& line, ParsedCommand& out) {
    memset(&out, 0, sizeof(out));
    String trimmed = line;
    trimmed.trim();
    if (trimmed.length() == 0) { out.type = CommandType::UNKNOWN; return false; }

    int sp = trimmed.indexOf(' ');
    String cmd = (sp < 0) ? trimmed : trimmed.substring(0, sp);
    String rest = (sp < 0) ? "" : trimmed.substring(sp + 1);
    rest.trim();
    cmd.toLowerCase();

    if (cmd == "help")        { out.type = CommandType::HELP; return true; }
    if (cmd == "status")      { out.type = CommandType::STATUS; return true; }
    if (cmd == "start")       { out.type = CommandType::START; return true; }
    if (cmd == "stop")        { out.type = CommandType::STOP; return true; }
    if (cmd == "reset")       { out.type = CommandType::RESET; return true; }
    if (cmd == "credentials") { out.type = CommandType::CREDENTIALS; return true; }

    if (cmd == "set") {
        int sp2 = rest.indexOf(' ');
        String key = (sp2 < 0) ? rest : rest.substring(0, sp2);
        String val = (sp2 < 0) ? "" : rest.substring(sp2 + 1);
        val.trim();
        key.toLowerCase();

        if (val.endsWith(" confirm")) {
            out.confirm = true;
            val = val.substring(0, val.length() - 8);
            val.trim();
        } else if (val == "confirm") {
            out.confirm = true;
            val = "";
        }

        if (key == "bssid") {
            out.type = CommandType::SET_BSSID;
            strncpy(out.arg1, val.c_str(), sizeof(out.arg1) - 1);
            return true;
        }
        if (key == "ssid") {
            out.type = CommandType::SET_SSID;
            strncpy(out.arg1, val.c_str(), sizeof(out.arg1) - 1);
            return true;
        }
        if (key == "channel") {
            out.type = CommandType::SET_CHANNEL;
            out.channel = (uint8_t)val.toInt();
            return true;
        }
    }

    out.type = CommandType::UNKNOWN;
    return false;
}

void serial_interface_init() {
    // Serial.begin() called in setup(); nothing to do here
}

void serial_interface_tick() {
    if (!Serial.available()) return;
    String line = Serial.readStringUntil('\n');
    ParsedCommand cmd;
    if (!parse_command(line, cmd)) {
        Serial.println(format_log("WARN", millis(), "Unknown command"));
        return;
    }
    switch (cmd.type) {
        case CommandType::STATUS:
            Serial.println(format_log("INFO", millis(), "CONFIG OK"));
            break;
        case CommandType::SET_BSSID:
            if (config_set_bssid(cmd.arg1, cmd.confirm)) {
                Serial.println(format_log("INFO", millis(), "BSSID set"));
            } else {
                Serial.println(format_log("WARN", millis(), "BSSID rejected by validator"));
            }
            break;
        case CommandType::SET_SSID:
            config_set_ssid(cmd.arg1);
            Serial.println(format_log("INFO", millis(), "SSID set"));
            break;
        default:
            Serial.println(format_log("INFO", millis(), "ACK"));
            break;
    }
}
