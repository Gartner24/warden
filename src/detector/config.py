"""DetectorConfig dataclass + argparse-based CLI parser."""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field

__all__ = ["DetectorConfig", "ConfigError", "parse_args"]

_BSSID_RE = re.compile(r"^[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}$")


class ConfigError(ValueError):
    """Raised when CLI arguments are invalid."""


@dataclass(frozen=True)
class DetectorConfig:
    iface: str
    pcap_file: str | None
    canal: int
    bssid_protegido: bytes
    ssid_protegido: str
    umbral_beacons_por_seg: int = 30
    ventana_beacon_seg: int = 5
    umbral_deauth_por_seg: int = 5
    ventana_deauth_seg: int = 3
    ventana_correlacion_seg: int = 60
    cooldown_alerta_seg: int = 5
    bssid_lista_blanca: tuple[bytes, ...] = field(default_factory=tuple)
    port: int = 8000


def _parse_bssid(s: str) -> bytes:
    if not _BSSID_RE.match(s):
        raise ConfigError(f"invalid BSSID: {s}")
    return bytes.fromhex(s.replace(":", ""))


def parse_args(argv: list[str]) -> DetectorConfig:
    p = argparse.ArgumentParser(prog="warden-detector")
    p.add_argument("--iface", default="panda0")
    p.add_argument("--pcap", dest="pcap_file", default=None)
    p.add_argument("--channel", dest="canal", type=int, default=6)
    p.add_argument("--bssid", required=True)
    p.add_argument("--ssid", required=True)
    p.add_argument("--umbral-beacons", dest="umbral_beacons_por_seg", type=int, default=30)
    p.add_argument("--ventana-beacon", dest="ventana_beacon_seg", type=int, default=5)
    p.add_argument("--umbral-deauth", dest="umbral_deauth_por_seg", type=int, default=5)
    p.add_argument("--ventana-deauth", dest="ventana_deauth_seg", type=int, default=3)
    p.add_argument("--ventana-corr", dest="ventana_correlacion_seg", type=int, default=60)
    p.add_argument("--cooldown", dest="cooldown_alerta_seg", type=int, default=5)
    p.add_argument("--port", type=int, default=8000)
    ns = p.parse_args(argv)

    if ns.pcap_file and "--iface" in argv:
        raise ConfigError("--iface and --pcap are mutually exclusive")
    if not (1 <= ns.canal <= 13):
        raise ConfigError(f"channel out of range: {ns.canal}")

    return DetectorConfig(
        iface=ns.iface,
        pcap_file=ns.pcap_file,
        canal=ns.canal,
        bssid_protegido=_parse_bssid(ns.bssid),
        ssid_protegido=ns.ssid,
        umbral_beacons_por_seg=ns.umbral_beacons_por_seg,
        ventana_beacon_seg=ns.ventana_beacon_seg,
        umbral_deauth_por_seg=ns.umbral_deauth_por_seg,
        ventana_deauth_seg=ns.ventana_deauth_seg,
        ventana_correlacion_seg=ns.ventana_correlacion_seg,
        cooldown_alerta_seg=ns.cooldown_alerta_seg,
        port=ns.port,
    )
