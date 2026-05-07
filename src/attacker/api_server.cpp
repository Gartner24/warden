#include "api_server.h"
#include "config.h"
#include <ArduinoJson.h>

static AsyncWebServer server(80);

static void send_not_implemented(AsyncWebServerRequest* req) {
    JsonDocument doc;
    doc["ok"] = false;
    doc["error"] = "not implemented";
    doc["codigo"] = "NOT_IMPLEMENTED";
    String body;
    serializeJson(doc, body);
    req->send(501, "application/json", body);
}

static void add_cors(AsyncWebServerResponse* resp) {
    resp->addHeader("Access-Control-Allow-Origin", "*");
    resp->addHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    resp->addHeader("Access-Control-Allow-Headers", "Content-Type");
}

void api_server_init() {
    server.on("/.*", HTTP_OPTIONS, [](AsyncWebServerRequest* req) {
        auto* resp = req->beginResponse(204);
        add_cors(resp);
        req->send(resp);
    });

    server.on("/status",          HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/attack/status",   HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/scan",            HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/clients",         HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/oui-lookup",      HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/config",          HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/config",          HTTP_POST, [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/attack/start",    HTTP_POST, [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/attack/stop",     HTTP_POST, [](AsyncWebServerRequest* req) { send_not_implemented(req); });
    server.on("/credentials",     HTTP_GET,  [](AsyncWebServerRequest* req) { send_not_implemented(req); });

    server.onNotFound([](AsyncWebServerRequest* req) {
        req->send(404, "application/json", "{\"ok\":false,\"error\":\"not found\",\"codigo\":\"NOT_FOUND\"}");
    });
}

void api_server_start() {
    api_server_init();
    server.begin();
}
