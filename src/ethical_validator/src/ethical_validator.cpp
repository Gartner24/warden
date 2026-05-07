#include "ethical_validator.h"
#include <string.h>

namespace warden {

static bool is_broadcast(const uint8_t b[6]) {
    for (int i = 0; i < 6; i++) if (b[i] != 0xFF) return false;
    return true;
}
static bool is_null(const uint8_t b[6]) {
    for (int i = 0; i < 6; i++) if (b[i] != 0x00) return false;
    return true;
}
static bool oui_in_blacklist(const uint8_t b[6], const uint8_t (*list)[3], size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (memcmp(b, list[i], 3) == 0) return true;
    }
    return false;
}

ValidationResult validate_bssid(const uint8_t bssid[6], bool confirm_provided, const ValidatorConfig& cfg) {
    if (is_broadcast(bssid)) return ValidationResult::REJECTED_BROADCAST;
    if (is_null(bssid)) return ValidationResult::REJECTED_NULL;
    if (cfg.lab_router_bssid && memcmp(bssid, *cfg.lab_router_bssid, 6) == 0) return ValidationResult::VALID;
    if (oui_in_blacklist(bssid, cfg.isp_oui_blacklist, cfg.isp_oui_blacklist_count))
        return ValidationResult::REJECTED_OUI_BLACKLIST;
    if (confirm_provided) return ValidationResult::VALID;
    return ValidationResult::REQUIRES_CONFIRMATION;
}

}  // namespace warden
