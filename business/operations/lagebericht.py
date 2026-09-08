#!/usr/bin/env python3
# CITED - taeglicher Lagebericht.
#
#   python3 lagebericht.py            Bericht auf den Bildschirm
#   python3 lagebericht.py --schreiben  DAILY_REPORT.md und STATUS.md erzeugen
#   python3 lagebericht.py --pruefen    zusaetzlich die Website anrufen
#
# Zwei Regeln, die dieses Werkzeug von einem huebschen Dashboard trennen:
#
#   1. Alle Geschaefts-Zahlen kommen aus status.json und werden dort VON
#      HAND gepflegt. Nichts wird geschaetzt, hochgerechnet oder
#      "modelliert". Steht dort eine Null, zeigt der Bericht eine Null.
#   2. Was nicht geprueft werden konnte, wird als NICHT GEPRUEFT
#      ausgewiesen - nie als in Ordnung.
#
# Der Bericht ist unangenehm, wenn nichts passiert. Das ist der Zweck.

import argparse
import datetime
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
STATUS = os.path.join(HIER, "status.json")

TRICHTER = [
    ("zielfirmen_gesammelt", "Zielfirmen gesammelt"),
    ("geprueft", "geprüft"),
    ("qualifiziert", "qualifiziert"),
    ("angerufen", "angerufen"),
    ("erreicht", "erreicht"),
    ("termin_vereinbart", "Termin vereinbart"),
    ("termin_gefuehrt", "Termin geführt"),
    ("angebot_gestellt", "Angebot gestellt"),
    ("kunden", "KUNDEN"),
]


def laden(pfad=STATUS):
    with open(pfad, encoding="utf-8") as f:
        return json.load(f)


def engpass(trichter):
    """Die erste Stufe, an der alles haengenbleibt.

    Gesucht ist der groesste Absturz zwischen zwei aufeinanderfolgenden
    Stufen. Bei lauter Nullen ist es die erste Stufe mit einer Null -
    dort faengt die Arbeit an.
    """
    werte = [(name, trichter.get(schluessel, 0))
             for schluessel, name in TRICHTER]
    for i in range(len(werte) - 1):
        oben, unten = werte[i], werte[i + 1]
        if oben[1] > 0 and unten[1] == 0:
            return "%s → %s" % (oben[0], unten[0])
    if werte[0][1] == 0:
        return "Noch nichts begonnen → %s" % werte[0][0]
    groesster, stelle = 0, None
    for i in range(len(werte) - 1):
        verlust = werte[i][1] - werte[i + 1][1]
        if verlust > groesster:
            groesster, stelle = verlust, "%s → %s" % (werte[i][0],
                                                      werte[i + 1][0])
    return stelle or "kein Engpass erkennbar"


def website_pruefen(url):
    """Echter Abruf. Ohne URL: NICHT GEPRUEFT, nicht 'in Ordnung'."""
    if not url:
        return ("NICHT GEPRÜFT", "Keine URL in status.json hinterlegt.")
    sys.path.insert(0, os.path.join(WURZEL, "product", "sichtbarkeit"))
    try:
        import netz
    except ImportError as e:
        return ("NICHT GEPRÜFT", "Netzmodul nicht ladbar: %s" % e)
    a = netz.holen(url, zeitlimit=15)
    if a.fehler:
        return ("FEHLGESCHLAGEN", a.fehler)
    if a.status != 200:
        return ("FEHLGESCHLAGEN", "Status %s" % a.status)
    return ("IN ORDNUNG", "Status 200 in %.2f s" % a.dauer)


def probleme(d):
    """Was auffaellt, ohne dass jemand es eintragen musste."""
    liste = []
    t = d["trichter"]
    g = d["geld"]
    z = d["zeit_diese_woche"]

    if t["kunden"] == 0 and t["angerufen"] == 0:
        liste.append("Null Anrufe. Ohne Gespräch entsteht kein Kunde — "
                     "kein Werkzeug und kein Text ändert daran etwas.")
    if t["geprueft"] > 0 and t["qualifiziert"] == 0:
        liste.append("Geprüft, aber nichts qualifiziert. Entweder sind die "
                     "Befunde zu gut (falsche Zielgruppe) oder die "
                     "Kriterien zu streng.")
    if t["angerufen"] >= 10 and t["termin_vereinbart"] == 0:
        liste.append("Zehn Anrufe ohne Termin. Nicht das Skript ändern — "
                     "zuerst prüfen, ob die Befunde wirklich schlecht sind.")
    if t["absagen"] >= 10:
        liste.append("Zehn Absagen. Jetzt die Begründungen auswerten: "
                     "wiederholt sich ein Satz, stimmt Angebot oder "
                     "Zielgruppe nicht.")
    if z["baustunden"] > 0 and z["verkaufsstunden"] * 3 < z["baustunden"]:
        liste.append("Bauzeit (%.1f h) über dreimal Verkaufszeit (%.1f h). "
                     "Das ist das bekannte Muster." %
                     (z["baustunden"], z["verkaufsstunden"]))
    if g["umsatz_chf"] == 0 and t["angebot_gestellt"] > 0:
        liste.append("Angebote draussen, kein Umsatz. Nachfassen steht an.")
    if not d["website"]["domain_registriert"]:
        liste.append("Keine eigene Domain. Für den ersten Kunden nicht "
                     "zwingend, für den zehnten schon.")
    return liste


def bericht_text(d, gesundheit=None):
    t = d["trichter"]
    g = d["geld"]
    z = d["zeit_diese_woche"]
    heute = datetime.date.today().strftime("%d.%m.%Y")
    hoechst = max(1, max(t.values()) if t.values() else 1)

    z_ = []
    a = z_.append
    a("# Lagebericht CITED — %s" % heute)
    a("")
    a("**Datenstand aus status.json: %s** · Phase: %s" % (d["stand"],
                                                          d["phase"]))
    a("")
    a("## Trichter")
    a("")
    a("| Stufe | Anzahl | |")
    a("|---|---:|---|")
    for schluessel, name in TRICHTER:
        wert = t.get(schluessel, 0)
        balken = "█" * int(round(18.0 * wert / hoechst)) if wert else ""
        a("| %s | %d | %s |" % (name, wert, balken))
    a("| Absagen | %d | |" % t.get("absagen", 0))
    a("")
    a("**Engpass:** %s" % engpass(t))
    a("")
    a("## Geld")
    a("")
    a("| | CHF |")
    a("|---|---:|")
    a("| Umsatz | %.2f |" % g["umsatz_chf"])
    a("| Kosten | %.2f |" % g["kosten_chf"])
    a("| **Gewinn** | **%.2f** |" % g["gewinn_chf"])
    a("| Wiederkehrend pro Monat | %.2f |" % g["wiederkehrend_chf_monat"])
    if g["kostenpositionen"]:
        a("")
        for p in g["kostenpositionen"]:
            a("- %s" % p)
    a("")
    a("## Zeit diese Woche")
    a("")
    a("- Verkauf: %.1f h" % z["verkaufsstunden"])
    a("- Bauen: %.1f h" % z["baustunden"])
    a("")
    a("## Website")
    a("")
    if gesundheit:
        lage, grund = gesundheit
        a("**STATUS: %s** — %s" % (lage, grund))
    else:
        a("**STATUS: NICHT GEPRÜFT** — mit `--pruefen` aufrufen.")
    a("")
    a("## Produktstand — was gebaut ist und was nicht")
    a("")
    for k, v in d["produkt"].items():
        marke = "✗" if v.upper().startswith("NICHT GEBAUT") else "✓"
        a("- %s **%s:** %s" % (marke, k.replace("_", " "), v))
    a("")
    p = probleme(d)
    a("## Erkannte Probleme")
    a("")
    if p:
        for x in p:
            a("- %s" % x)
    else:
        a("- Keine.")
    a("")
    a("## Blockiert")
    a("")
    for x in d["blockiert"]:
        a("- %s" % x)
    a("")
    a("## Nächste Aktion")
    a("")
    if d["naechste_aktionen"]:
        a("**%s**" % d["naechste_aktionen"][0])
        a("")
        for x in d["naechste_aktionen"][1:]:
            a("- %s" % x)
    else:
        a("- Keine eingetragen.")
    a("")
    a("---")
    a("")
    a("*Erzeugt aus status.json. Alle Geschäftszahlen sind von Hand "
      "gepflegt; nichts ist geschätzt oder hochgerechnet.*")
    return "\n".join(z_)


def status_text(d, gesundheit=None):
    t = d["trichter"]
    g = d["geld"]
    fertig = [k for k, v in d["produkt"].items()
              if not v.upper().startswith("NICHT GEBAUT")]
    offen = [k for k, v in d["produkt"].items()
             if v.upper().startswith("NICHT GEBAUT")]
    lage = gesundheit[0] if gesundheit else "NICHT GEPRÜFT"
    return "\n".join([
        "# STATUS",
        "",
        "**CURRENT PHASE:** %s" % d["phase"],
        "",
        "**CURRENT OBJECTIVE:** %s" % d["ziel"],
        "",
        "**COMPLETED:** " + ", ".join(k.replace("_", " ") for k in fertig),
        "",
        "**IN PROGRESS:** Zielfirmen sammeln und Kurzbefunde erstellen",
        "",
        "**NOT BUILT (ausdrücklich):** " +
        ", ".join(k.replace("_", " ") for k in offen),
        "",
        "**BLOCKERS:**",
        "",
    ] + ["- %s" % x for x in d["blockiert"]] + [
        "",
        "**NEXT ACTION:** %s" % (d["naechste_aktionen"][0]
                                 if d["naechste_aktionen"] else "—"),
        "",
        "**REAL-WORLD METRICS:**",
        "",
        "| Kennzahl | Wert |",
        "|---|---:|",
        "| Zielfirmen geprüft | %d |" % t["geprueft"],
        "| Angerufen | %d |" % t["angerufen"],
        "| Termine geführt | %d |" % t["termin_gefuehrt"],
        "| **Kunden** | **%d** |" % t["kunden"],
        "| Umsatz CHF | %.2f |" % g["umsatz_chf"],
        "| Kosten CHF | %.2f |" % g["kosten_chf"],
        "| Gewinn CHF | %.2f |" % g["gewinn_chf"],
        "| Website | %s |" % lage,
        "",
        "*Stand %s. Erzeugt aus operations/status.json.*"
        % datetime.date.today().strftime("%d.%m.%Y"),
        "",
    ])


def main(argumente):
    p = argparse.ArgumentParser(prog="lagebericht")
    p.add_argument("--schreiben", action="store_true",
                   help="DAILY_REPORT.md und STATUS.md erzeugen")
    p.add_argument("--pruefen", action="store_true",
                   help="Website tatsaechlich abrufen")
    p.add_argument("--status", default=STATUS)
    args = p.parse_args(argumente)

    try:
        d = laden(args.status)
    except (OSError, ValueError) as e:
        print("STATUS: FEHLGESCHLAGEN", file=sys.stderr)
        print("GRUND: status.json nicht lesbar: %s" % e, file=sys.stderr)
        print("BELEG: %s" % args.status, file=sys.stderr)
        print("FIX: Datei pruefen oder aus der Versionsverwaltung holen.",
              file=sys.stderr)
        return 1

    gesundheit = website_pruefen(d["website"]["url"]) if args.pruefen else None
    text = bericht_text(d, gesundheit)

    if args.schreiben:
        with open(os.path.join(WURZEL, "DAILY_REPORT.md"), "w",
                  encoding="utf-8") as f:
            f.write(text + "\n")
        with open(os.path.join(WURZEL, "STATUS.md"), "w",
                  encoding="utf-8") as f:
            f.write(status_text(d, gesundheit))
        print("Geschrieben: business/DAILY_REPORT.md, business/STATUS.md")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        os._exit(0)
