"""D-03: detect rogue AP cloning protected SSID with new BSSID."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from detector.config import DetectorConfig

__all__ = ["EvilTwinAnalyzer"]


class EvilTwinAnalyzer:
    def __init__(self, config: DetectorConfig) -> None:
        self._ssid_protegido = config.ssid_protegido
        self._bssid_protegido = config.bssid_protegido
        self._whitelist = set(config.bssid_lista_blanca)
        self._emitted: set[tuple[str, bytes]] = set()
        self._pending: list[dict[str, Any]] = []

    def observe(self, pkt: object, ts: datetime) -> None:
        from scapy.layers.dot11 import Dot11, Dot11Elt
        bssid_str = pkt[Dot11].addr2  # type: ignore[index]
        if not bssid_str:
            return
        bssid = bytes.fromhex(bssid_str.replace(":", ""))
        ssid: str | None = None
        elt = pkt.getlayer(Dot11Elt)  # type: ignore[attr-defined]
        while elt is not None:
            if elt.ID == 0:
                ssid = elt.info.decode("utf-8", errors="replace")
                break
            elt = elt.payload.getlayer(Dot11Elt)
        if ssid is None:
            return
        if ssid != self._ssid_protegido:
            return
        if bssid == self._bssid_protegido or bssid in self._whitelist:
            return
        if (ssid, bssid) in self._emitted:
            return
        self._emitted.add((ssid, bssid))
        self._pending.append({
            "timestamp": ts.isoformat(),
            "severidad": "CRITICAL",
            "tipo": "EVIL_TWIN",
            "mensaje": f"Posible Evil Twin para SSID '{ssid}'",
            "detalles": {
                "ssid": ssid,
                "bssid_legitimo": self._bssid_protegido.hex(":"),
                "bssid_clon": bssid.hex(":"),
            },
        })

    def drain(self) -> list[dict[str, Any]]:
        out, self._pending = self._pending, []
        return out
