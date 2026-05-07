#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"
// frame_builder.h and .cpp are in src/attacker/ - include via relative path
#include "../../attacker/frame_builder.h"
// Implementation is a separate TU; include it directly for host build
#include "../../attacker/frame_builder.cpp"

#include <string.h>
#include <stdint.h>

TEST_CASE("beacon frame minimum size") {
    uint8_t buf[256] = {0};
    uint8_t bssid[6] = {0xAA,0xBB,0xCC,0xDD,0xEE,0xFF};
    size_t len = build_beacon_frame(buf, sizeof(buf), bssid, "TEST", 6);
    CHECK(len > 24);  // at least header (24) + minimal body
    // Frame control byte 0 = 0x80 (beacon)
    CHECK(buf[0] == 0x80);
    CHECK(buf[1] == 0x00);
    // Addr1 = broadcast
    for (int i = 0; i < 6; i++) CHECK(buf[4+i] == 0xFF);
    // Addr2 = bssid
    CHECK(memcmp(buf+10, bssid, 6) == 0);
}

TEST_CASE("beacon frame SSID IE present") {
    uint8_t buf[256] = {0};
    uint8_t bssid[6] = {0x11,0x22,0x33,0x44,0x55,0x66};
    const char* ssid = "TestNet";
    size_t len = build_beacon_frame(buf, sizeof(buf), bssid, ssid, 1);
    CHECK(len > 0);
    // After 24-byte header + 12-byte fixed body (ts+interval+cap), SSID IE starts at offset 36
    CHECK(buf[36] == 0x00);           // SSID IE ID
    CHECK(buf[37] == 7);              // SSID length
    CHECK(memcmp(buf+38, "TestNet", 7) == 0);
}

TEST_CASE("deauth frame size and FC") {
    uint8_t buf[128] = {0};
    uint8_t target[6] = {0x11,0x22,0x33,0x44,0x55,0x66};
    uint8_t bssid[6]  = {0xAA,0xBB,0xCC,0xDD,0xEE,0xFF};
    size_t len = build_deauth_frame(buf, sizeof(buf), target, bssid, 7);
    CHECK(len == 26);  // 24 header + 2 reason
    CHECK(buf[0] == 0xC0);
    CHECK(buf[1] == 0x00);
    // Addr1 = target
    CHECK(memcmp(buf+4, target, 6) == 0);
    // Addr2 = bssid (spoofed)
    CHECK(memcmp(buf+10, bssid, 6) == 0);
    // reason code = 7 LE
    CHECK(buf[24] == 0x07);
    CHECK(buf[25] == 0x00);
}

TEST_CASE("buffer too small returns 0") {
    uint8_t buf[10];
    uint8_t bssid[6] = {0};
    CHECK(build_beacon_frame(buf, sizeof(buf), bssid, "X", 6) == 0);
    uint8_t target[6] = {0};
    CHECK(build_deauth_frame(buf, sizeof(buf), target, bssid, 7) == 0);
}
