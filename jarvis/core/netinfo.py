"""Netzwerk-Hilfen für den Handy-Zugang (LAN-IP ermitteln)."""

from __future__ import annotations

import socket


def lan_ip() -> str:
    """Ermittelt die LAN-IP dieses PCs (die Adresse, unter der das Handy im
    selben WLAN JARVIS erreicht). Ohne echten Traffic: ein UDP-Socket 'verbindet'
    sich nur, um die passende ausgehende Adresse zu erfahren.

    Gibt '' zurück, wenn keine sinnvolle (nicht-Loopback) Adresse gefunden wird.
    """
    ip = ""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))       # kein Paket, nur Routing-Wahl
            ip = s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        ip = ""
    if not ip or ip.startswith("127."):
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip = ""
    return "" if ip.startswith("127.") else ip
