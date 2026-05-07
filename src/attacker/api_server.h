#pragma once
#include <ESPAsyncWebServer.h>

void api_server_init();
void api_server_start();
void emit_event(const char* type, const char* json_payload);
void cred_push(const char* user, const char* pass, const char* ip);
