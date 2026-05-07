#pragma once
#include <stdint.h>
#include <stddef.h>

bool lookup_oui(const uint8_t mac[6], char* vendor_out, size_t cap);
