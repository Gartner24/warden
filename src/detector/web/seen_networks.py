"""Passive tracker of beacons/probe-responses seen on the monitor interface."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt

__all__ = ["SeenNetworks"]


class SeenNetworks:
    def __init__(self) -> None:
        self._nets: dict[bytes, dict[str, Any]] = {}

    def observe(self, pkt: object) -> None:
        if not (pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp)):  # type: ignore[attr-defined]
            return
        dot11 = pkt.getlayer(Dot11)  # type: ignore[attr-defined]
        if dot11 is None or dot11.addr2 is None:
            return
        bssid_str: str = dot11.addr2
        try:
            bssid_bytes = bytes.fromhex(bssid_str.replace(":", ""))
        except ValueError:
            return
        # Extract SSID from first Dot11Elt ID=0
        ssid = ""
        elt = pkt.getlayer(Dot11Elt)  # type: ignore[attr-defined]
        while elt is not None:
            if elt.ID == 0:
                try:
                    ssid = elt.info.decode("utf-8", errors="replace")
                except Exception:
                    ssid = ""
                break
            elt = elt.payload.getlayer(Dot11Elt)
        # Extract channel from DS Parameter Set (Dot11Elt ID=3)
        channel: int | None = None
        elt = pkt.getlayer(Dot11Elt)  # type: ignore[attr-defined]
        while elt is not None:
            if elt.ID == 3 and len(elt.info) >= 1:
                channel = elt.info[0]
                break
            elt = elt.payload.getlayer(Dot11Elt)
        # RSSI from RadioTap if available
        rssi: int | None = None
        try:
            rssi = pkt.dBm_AntSignal  # type: ignore[attr-defined]
        except AttributeError:
            pass
        now = datetime.now(timezone.utc).isoformat()
        if bssid_bytes in self._nets:
            entry = self._nets[bssid_bytes]
            entry["last_seen"] = now
            entry["hit_count"] = entry.get("hit_count", 0) + 1
            if rssi is not None:
                entry["rssi"] = rssi
            if channel is not None:
                entry["channel"] = channel
            if ssid and not entry.get("ssid"):
                entry["ssid"] = ssid
        else:
            self._nets[bssid_bytes] = {
                "bssid": bssid_str,
                "ssid": ssid,
                "channel": channel,
                "rssi": rssi,
                "first_seen": now,
                "last_seen": now,
                "hit_count": 1,
            }

    def snapshot(self) -> list[dict[str, Any]]:
        return sorted(
            self._nets.values(),
            key=lambda e: e.get("hit_count", 0),
            reverse=True,
        )
