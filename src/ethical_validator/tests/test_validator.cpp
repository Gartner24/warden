#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
#include "ethical_validator.h"

using warden::ValidationResult;
using warden::validate_bssid;
using warden::ValidatorConfig;

static const uint8_t LAB_BSSID[6] = {0xE4,0xAB,0x89,0xD6,0x9B,0x80};
static const uint8_t TIGO_OUI[][3] = { {0x10,0x05,0xCA}, {0xC4,0x6E,0x1F} };

static ValidatorConfig make_cfg() {
    ValidatorConfig c{};
    c.lab_router_bssid = &LAB_BSSID;
    c.isp_oui_blacklist = TIGO_OUI;
    c.isp_oui_blacklist_count = 2;
    return c;
}

TEST_CASE("broadcast rejected") {
    uint8_t b[6] = {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF};
    CHECK(validate_bssid(b, true, make_cfg()) == ValidationResult::REJECTED_BROADCAST);
}

TEST_CASE("null rejected") {
    uint8_t b[6] = {0,0,0,0,0,0};
    CHECK(validate_bssid(b, true, make_cfg()) == ValidationResult::REJECTED_NULL);
}

TEST_CASE("ISP OUI rejected") {
    uint8_t b[6] = {0x10,0x05,0xCA,0x11,0x22,0x33};
    CHECK(validate_bssid(b, true, make_cfg()) == ValidationResult::REJECTED_OUI_BLACKLIST);
}

TEST_CASE("second OUI in blacklist is rejected") {
    uint8_t b[6] = {0xC4,0x6E,0x1F,0x11,0x22,0x33};
    CHECK(validate_bssid(b, true, make_cfg()) == ValidationResult::REJECTED_OUI_BLACKLIST);
}

TEST_CASE("lab router auto-valid") {
    CHECK(validate_bssid(LAB_BSSID, false, make_cfg()) == ValidationResult::VALID);
}

TEST_CASE("any other BSSID requires confirmation") {
    uint8_t b[6] = {0xAA,0xBB,0xCC,0xDD,0xEE,0xFF};
    CHECK(validate_bssid(b, false, make_cfg()) == ValidationResult::REQUIRES_CONFIRMATION);
}

TEST_CASE("with confirmation any non-blacklisted BSSID is valid") {
    uint8_t b[6] = {0xAA,0xBB,0xCC,0xDD,0xEE,0xFF};
    CHECK(validate_bssid(b, true, make_cfg()) == ValidationResult::VALID);
}
