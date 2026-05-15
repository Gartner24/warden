#pragma once
#include <ESPAsyncWebServer.h>

void api_server_init();
void api_server_start();
void api_server_pause();
void api_server_resume();
void emit_event(const char* type, const char* json_payload);
void cred_push(const char* user, const char* pass, const char* ip);
void cred_reset();
AsyncWebServer& api_server_get();
