#include "oui_lookup.h"
#include "oui_database.h"
#include <string.h>
#include <pgmspace.h>

bool lookup_oui(const uint8_t mac[6], char* vendor_out, size_t cap) {
    uint16_t lo = 0, hi = OUI_COUNT;
    while (lo < hi) {
        uint16_t mid = lo + (hi - lo) / 2;
        OuiEntry entry;
        memcpy_P(&entry, &OUI_TABLE[mid], sizeof(OuiEntry));
        int cmp = memcmp(mac, entry.prefix, 3);
        if (cmp == 0) {
            strncpy(vendor_out, entry.vendor, cap - 1);
            vendor_out[cap - 1] = '\0';
            return true;
        } else if (cmp < 0) {
            hi = mid;
        } else {
            lo = mid + 1;
        }
    }
    strncpy(vendor_out, "Fabricante desconocido", cap - 1);
    vendor_out[cap - 1] = '\0';
    return false;
}
