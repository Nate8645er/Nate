#!/usr/bin/env python3
# SETTLED - Krypto-Zahlungsabgleich fuer Onlinehaendler.
#
#   python3 settled.py ketten
#   python3 settled.py eingaenge --adresse <adr> --waehrung USDT-TRC20
#   python3 settled.py abgleich --bestellungen b.csv \
#       --adresse <adr> --waehrung USDT-TRC20 --fiat chf
#
# Liest nur. Bewegt kein Geld. Verlangt keinen privaten Schluessel.

import argparse
import csv
import datetime
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import abgleich          # noqa: E402
import ketten            # noqa: E402
import kurse             # noqa: E402

ZEICHEN = {abgleich.BEZAHLT: "+", abgleich.UNTERBEZAHLT: "!",
           abgleich.UEBERBEZAHLT: "^", abgleich.OFFEN: "-",
           abgleich.UNERWARTET: "?"}


def _zeit(t):
    return datetime.datetime.fromtimestamp(
        t, datetime.timezone.utc).strftime("%d.%m.%Y %H:%M")


def _kurs_funktion(waehrung, zeit, fiat):
    t = ketten.TOKEN.get(waehrung)
    if not t or "coingecko" not in t:
        raise kurse.KursFehler("Kein Kursbezug fuer %s" % waehrung)
    return kurse.tageskurs(t["coingecko"], zeit, fiat)


def befehl_ketten(args):
    zeilen = []
    for name, t in sorted(ketten.TOKEN.items()):
        zeilen.append({"waehrung": name, "kette": t["kette"],
                       "dezimalen": t["dezimalen"],
                       "vertrag": t.get("vertrag", "-")})
    return {"unterstuetzt": zeilen,
            "nicht_abgedeckt": "natives ETH (braucht einen kostenpflichtigen "
                               "Indexer) - wird nie als 'keine Zahlungen' "
                               "ausgegeben, sondern als Luecke gemeldet"}


def befehl_eingaenge(args):
    seit = abgleich.zeit_lesen(args.seit) if args.seit else 0
    e = ketten.eingaenge_lesen(args.adresse, args.waehrung, seit)
    e.sort(key=lambda x: x.zeit, reverse=True)
    return {"adresse": args.adresse, "waehrung": args.waehrung,
            "anzahl": len(e), "eingaenge": [x.als_daten() for x in e]}


def befehl_abgleich(args):
    bestellungen = abgleich.bestellungen_lesen(args.bestellungen)
    if not bestellungen:
        raise ValueError("Keine Bestellungen in %s" % args.bestellungen)

    seit = min(b.zeit for b in bestellungen) - abgleich.FENSTER_VOR
    eingaenge = ketten.eingaenge_lesen(args.adresse, args.waehrung, seit)

    zeilen = abgleich.zuordnen(bestellungen, eingaenge)
    if not args.ohne_kurse:
        abgleich.bewerten(zeilen, _kurs_funktion, args.fiat)

    if args.csv:
        _csv_schreiben(args.csv, zeilen, args.fiat)

    return {"bestellungen": len(bestellungen),
            "eingaenge": len(eingaenge),
            "zusammenfassung": abgleich.zusammenfassen(zeilen, args.fiat),
            "zeilen": [_zeile_als_daten(z) for z in zeilen],
            "csv": args.csv}


def _zeile_als_daten(z):
    b, e = z.get("bestellung"), z.get("eingang")
    return {
        "status": z["status"],
        "bestellnummer": b.nummer if b else None,
        "soll": round(b.betrag, 8) if b else None,
        "ist": round(e.betrag, 8) if e else None,
        "waehrung": (b or e).waehrung,
        "differenz": round(z["differenz"], 8),
        "eingang_am": _zeit(e.zeit) if e else None,
        "tx": e.tx if e else None,
        "kurs": z.get("kurs"),
        "fiat": z.get("fiat"),
        "kurs_fehler": z.get("kurs_fehler"),
    }


def _csv_schreiben(pfad, zeilen, fiat):
    ordner = os.path.dirname(os.path.abspath(pfad))
    if ordner:
        os.makedirs(ordner, exist_ok=True)
    with open(pfad, "w", encoding="utf-8", newline="") as f:
        s = csv.writer(f, delimiter=";")
        s.writerow(["status", "bestellnummer", "soll", "ist", "waehrung",
                    "differenz", "eingang_am", "kurs_" + fiat.lower(),
                    "wert_" + fiat.lower(), "tx", "hinweis"])
        for z in zeilen:
            d = _zeile_als_daten(z)
            s.writerow([d["status"], d["bestellnummer"], d["soll"], d["ist"],
                        d["waehrung"], d["differenz"], d["eingang_am"],
                        d["kurs"], d["fiat"], d["tx"],
                        d["kurs_fehler"] or ""])


def ausgeben(daten, als_json):
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return
    if "zeilen" in daten:
        z = daten["zusammenfassung"]
        print("Bestellungen: %d   Kettenzahlungen: %d"
              % (daten["bestellungen"], daten["eingaenge"]))
        print()
        for d in daten["zeilen"]:
            print("  %s %-10s %-12s soll %-14s ist %-14s %s"
                  % (ZEICHEN.get(d["status"], " "), d["status"],
                     d["bestellnummer"] or "-",
                     ("%.6f" % d["soll"]) if d["soll"] is not None else "-",
                     ("%.6f" % d["ist"]) if d["ist"] is not None else "-",
                     ("%s %.2f" % (z["fiat"], d["fiat"]))
                     if d["fiat"] is not None else
                     ("Kurs fehlt" if d["ist"] is not None else "")))
        print()
        print("  bezahlt %d · unterbezahlt %d · ueberbezahlt %d · offen %d "
              "· unerwartet %d" % (z["bezahlt"], z["unterbezahlt"],
                                   z["ueberbezahlt"], z["offen"],
                                   z["unerwartet"]))
        print("  Buchwert %s %.2f" % (z["fiat"], z["fiat_summe"]))
        if z["unbewertet"]:
            print("  NICHT BEWERTET: %d Zahlung(en) ohne Kurs" % z["unbewertet"])
        if daten.get("csv"):
            print("  geschrieben: %s" % daten["csv"])
        return
    for schluessel, wert in daten.items():
        if isinstance(wert, list):
            print("%s:" % schluessel)
            for x in wert:
                print("   %s" % (json.dumps(x, ensure_ascii=False)
                                 if isinstance(x, dict) else x))
        else:
            print("%-16s %s" % (schluessel + ":", wert))


def main(argumente):
    gemeinsam = argparse.ArgumentParser(add_help=False)
    gemeinsam.add_argument("--json", action="store_true")

    p = argparse.ArgumentParser(
        prog="settled", parents=[gemeinsam],
        description="Krypto-Zahlungen gegen Bestellungen abgleichen.")
    unter = p.add_subparsers(dest="befehl", required=True)

    unter.add_parser("ketten", parents=[gemeinsam],
                     help="Welche Ketten und Token abgedeckt sind")

    a = unter.add_parser("eingaenge", parents=[gemeinsam],
                         help="Zahlungseingaenge einer Adresse zeigen")
    a.add_argument("--adresse", required=True)
    a.add_argument("--waehrung", required=True)
    a.add_argument("--seit", help="Datum, z.B. 2026-08-01")

    b = unter.add_parser("abgleich", parents=[gemeinsam],
                         help="Bestellungen gegen die Kette abgleichen")
    b.add_argument("--bestellungen", required=True, help="CSV")
    b.add_argument("--adresse", required=True)
    b.add_argument("--waehrung", required=True)
    b.add_argument("--fiat", default="chf")
    b.add_argument("--csv", help="Ergebnis als CSV schreiben")
    b.add_argument("--ohne-kurse", action="store_true",
                   help="Keine Bewertung (schneller, ohne Netzzugriff)")

    args = p.parse_args(argumente)
    als_json = args.json or "--json" in argumente

    befehle = {"ketten": befehl_ketten, "eingaenge": befehl_eingaenge,
               "abgleich": befehl_abgleich}
    try:
        ergebnis = befehle[args.befehl](args)
    except (ketten.KettenFehler, kurse.KursFehler, ValueError, OSError) as e:
        if als_json:
            print(json.dumps({"fehler": str(e)}, ensure_ascii=False))
        else:
            print("Fehler: %s" % e, file=sys.stderr)
        return 1
    ausgeben(ergebnis, als_json)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        os._exit(0)
