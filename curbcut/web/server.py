#!/usr/bin/env python3
"""
server.py - die kostenlose Pruefung, die den Vertrieb macht.

    python3 web/server.py          # laeuft auf http://localhost:8080

WARUM DAS DER VERTRIEB IST UND NICHT NUR EINE DEMO

Nate kann nicht verkaufen. Zwei Anlaeufe, null Kunden, beide Male am
selben Punkt gescheitert: Es gab niemanden, der von sich aus kam.

Ein Verkaufsgespraech muss jemanden erst davon ueberzeugen, dass er ein
Problem hat. Diese Seite ueberspringt das: Der Besucher tippt seine
eigene Adresse ein und sieht in acht Sekunden seine eigenen Fehler, mit
seinem eigenen Quelltext daneben. Danach muss ihn niemand mehr
ueberzeugen - er hat es selbst gesehen.

Das Werkzeug macht sichtbar, was vorher unsichtbar war. Das ist der
ganze Trick, und es ist der einzige Vertriebsweg, der ohne Nate
funktioniert.

WAS HIER BEWUSST FEHLT

Keine Zaehler, die hochlaufen. Keine erfundenen Kundenstimmen. Keine
Dringlichkeit. Wer ein Werkzeug verkauft, das sich darueber definiert,
nicht zu luegen, darf auf der Verkaufsseite nicht anfangen.
"""

import html
import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "kern"))

from bauteile import buendeln
from befund import DIE_SECHS
from pruefen import von_url
from seite import NichtErreichbar

ANSCHRIFT = ("0.0.0.0", int(os.environ.get("PORT", 8080)))


def seite_lesen(name):
    with open(os.path.join(HIER, name), encoding="utf-8") as f:
        return f.read()


def befund_html(url):
    """Der Kern: aus einer Adresse wird ein lesbarer Befund."""
    try:
        b = von_url(url)
    except NichtErreichbar as e:
        return {"fehler": str(e)}

    teile = buendeln(b.befunde)
    sperrend = sum(1 for t in teile if t.schwere == "sperrend")

    return {
        "url": b.shop,
        "stellen": len(teile),
        "vorkommen": len(b.befunde),
        "sperrend": sperrend,
        "funde": [
            {
                "titel": DIE_SECHS[t.art][0],
                "kriterium": DIE_SECHS[t.art][2],
                "anteil": DIE_SECHS[t.art][1],
                "schwere": t.schwere,
                "wo": t.beschreiben(),
                "anzahl": t.anzahl,
                "stelle": t.erster.stelle,
                "rat": t.erster.vorschlag,
            }
            for t in teile[:12]
        ],
        "mehr": max(0, len(teile) - 12),
    }


class Griff(BaseHTTPRequestHandler):
    def _senden(self, koerper, art="text/html; charset=utf-8", code=200):
        roh = koerper.encode("utf-8") if isinstance(koerper, str) else koerper
        self.send_response(code)
        self.send_header("Content-Type", art)
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(roh)

    def do_GET(self):
        weg = urllib.parse.urlparse(self.path)

        if weg.path == "/":
            return self._senden(seite_lesen("start.html"))

        if weg.path == "/pruefen":
            frage = urllib.parse.parse_qs(weg.query)
            url = (frage.get("url") or [""])[0].strip()
            if not url:
                return self._senden(json.dumps({"fehler": "Keine Adresse angegeben."}),
                                    "application/json; charset=utf-8", 400)
            # Nur oeffentliche Adressen. Ohne das kann jemand den Server
            # dazu bringen, sein eigenes internes Netz abzufragen.
            if not _oeffentlich(url):
                return self._senden(
                    json.dumps({"fehler": "Nur oeffentlich erreichbare Adressen."}),
                    "application/json; charset=utf-8", 400)
            ergebnis = befund_html(url)
            return self._senden(json.dumps(ergebnis, ensure_ascii=False),
                                "application/json; charset=utf-8")

        if weg.path == "/bot":
            return self._senden(seite_lesen("bot.html"))

        return self._senden("Nicht gefunden", "text/plain; charset=utf-8", 404)

    def log_message(self, *a):
        pass          # keine Adressen mitschreiben


VERBOTEN = ("localhost", "127.", "0.0.0.0", "10.", "192.168.", "169.254.",
            "[::1]", "metadata.", "::1")


def _oeffentlich(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    wirt = urllib.parse.urlparse(url).hostname or ""
    wirt = wirt.lower()
    if any(wirt.startswith(v) or wirt == v.rstrip(".") for v in VERBOTEN):
        return False
    if wirt.startswith("172."):
        try:
            zweit = int(wirt.split(".")[1])
            if 16 <= zweit <= 31:
                return False
        except (ValueError, IndexError):
            return False
    return "." in wirt


if __name__ == "__main__":
    server = HTTPServer(ANSCHRIFT, Griff)
    print(f"  Curbcut laeuft auf http://localhost:{ANSCHRIFT[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  beendet")
