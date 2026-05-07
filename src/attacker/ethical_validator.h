#pragma once
#include <stdint.h>
#include <stddef.h>

namespace warden {

enum class ValidationResult : uint8_t {
    VALID,
    REJECTED_BROADCAST,
    REJECTED_NULL,
    REJECTED_OUI_BLACKLIST,
    REQUIRES_CONFIRMATION,
};

struct ValidatorConfig {
    const uint8_t (*lab_router_bssid)[6];
    const uint8_t (*isp_oui_blacklist)[3];
    size_t isp_oui_blacklist_count;
};

ValidationResult validate_bssid(const uint8_t bssid[6],
                                bool confirm_provided,
                                const ValidatorConfig& cfg);

}  // namespace warden
