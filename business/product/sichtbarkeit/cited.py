#!/usr/bin/env python3
# CITED - Kommandozeile.
#
#   python3 cited.py pruefen beispiel.ch
#   python3 cited.py fragen --firma "Meier Treuhand AG" --domain meier.ch \
#       --branche Treuhandbuero --ort Rapperswil \
#       --leistung Buchhaltung --leistung Steuererklaerung \
#       --datei erhebungen/meier.json
#   python3 cited.py erfassen --datei erhebungen/meier.json \
#       --system ChatGPT --frage 1 --antwort-datei antwort.txt
#   python3 cited.py bericht --datei erhebungen/meier.json --ausgabe meier.html
#
# Der Ablauf ist bewusst dreiteilig: pruefen laeuft in Sekunden und ohne
# Vorbereitung - das ist der Kurzbefund fuer die Ansprache. Erst wenn
# jemand kauft, lohnt sich die Erfassung der Antworten.

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import bericht          # noqa: E402
import fragen as fragen_modul  # noqa: E402
import netz             # noqa: E402
import technik          # noqa: E402


def befehl_pruefen(args):
    basis = netz.domain_normalisieren(args.domain)
    befunde, _ = technik.pruefen(basis)
    erreicht, moeglich, prozent = technik.punkte(befunde)
    return {
        "domain": basis,
        "punkte": "%d/%d" % (erreicht, moeglich),
        "prozent": prozent,
        "befunde": [b.als_daten() for b in befunde],
    }


def befehl_fragen(args):
    basis = netz.domain_normalisieren(args.domain)
    liste = fragen_modul.fragen_bauen(
        args.branche, args.ort, args.leistung,
        region=args.region, zusatz=args.zusatz, anzahl=args.anzahl)
    e = fragen_modul.Erhebung(args.datei).anlegen(args.firma, basis, liste)
    e.sichern()
    return {"datei": args.datei, "firma": args.firma, "domain": basis,
            "fragen": liste}


def befehl_erfassen(args):
    e = fragen_modul.Erhebung(args.datei)
    if not e.daten.get("fragen"):
        raise ValueError("In %s stehen keine Fragen. Zuerst 'fragen' "
                         "ausfuehren." % args.datei)
    if not 1 <= args.frage <= len(e.daten["fragen"]):
        raise ValueError("Frage %d gibt es nicht (1 bis %d)."
                         % (args.frage, len(e.daten["fragen"])))
    if args.antwort_datei:
        with open(args.antwort_datei, encoding="utf-8") as f:
            wortlaut = f.read()
    else:
        wortlaut = sys.stdin.read()
    if not wortlaut.strip():
        raise ValueError("Leere Antwort - nichts erfasst.")

    frage = e.daten["fragen"][args.frage - 1]
    eintrag = e.erfassen(args.system, frage, wortlaut.strip(),
                         args.quelle or [])
    e.sichern()
    return {"erfasst": args.system, "frage": frage,
            "zeichen": len(eintrag["wortlaut"]),
            "firma_genannt": fragen_modul.genannt(
                eintrag["wortlaut"], e.daten["firma"], e.daten["domain"]),
            "antworten_gesamt": len(e.daten["antworten"])}


def befehl_bericht(args):
    e = fragen_modul.Erhebung(args.datei) if args.datei and \
        os.path.exists(args.datei) else None
    domain = args.domain or (e.daten["domain"] if e else None)
    firma = args.firma or (e.daten["firma"] if e else domain)
    if not domain:
        raise ValueError("Weder --domain noch eine Erhebung angegeben.")
    basis = netz.domain_normalisieren(domain)

    befunde, _ = technik.pruefen(basis)
    auswertung = fragen_modul.auswerten(e) if e else None
    seite = bericht.bauen(firma, basis, befunde, technik.punkte(befunde),
                          e, auswertung)
    ordner = os.path.dirname(os.path.abspath(args.ausgabe))
    if ordner:
        os.makedirs(ordner, exist_ok=True)
    with open(args.ausgabe, "w", encoding="utf-8") as f:
        f.write(seite)
    return {"bericht": args.ausgabe, "firma": firma, "domain": basis,
            "prozent": technik.punkte(befunde)[2],
            "antworten": len(e.daten["antworten"]) if e else 0}


def ausgeben(daten, als_json):
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return
    for schluessel, wert in daten.items():
        if schluessel == "befunde":
            print()
            for b in wert:
                zeichen = {True: "+", False: "!", None: "?"}[b["bestanden"]]
                print("  %s %-22s %s" % (zeichen, b["feld"], b["aussage"]))
                if b["massnahme"] and b["bestanden"] is not True:
                    print("      -> %s" % b["massnahme"])
            continue
        if isinstance(wert, list):
            print("%-16s" % (schluessel + ":"))
            for i, x in enumerate(wert, 1):
                print("   %2d. %s" % (i, x))
        else:
            print("%-16s %s" % (schluessel + ":", wert))


def main(argumente):
    gemeinsam = argparse.ArgumentParser(add_help=False)
    gemeinsam.add_argument("--json", action="store_true",
                           help="Maschinenlesbare Ausgabe")

    p = argparse.ArgumentParser(
        prog="cited", parents=[gemeinsam],
        description="KI-Sichtbarkeit einer Website pruefen.")
    unter = p.add_subparsers(dest="befehl", required=True)

    a = unter.add_parser("pruefen", parents=[gemeinsam],
                         help="Technische Auffindbarkeit (Kurzbefund)")
    a.add_argument("domain")

    b = unter.add_parser("fragen", parents=[gemeinsam],
                         help="Fragensatz erzeugen und Erhebung anlegen")
    b.add_argument("--firma", required=True)
    b.add_argument("--domain", required=True)
    b.add_argument("--branche", required=True)
    b.add_argument("--ort", required=True)
    b.add_argument("--leistung", action="append", required=True,
                   help="Mehrfach angeben")
    b.add_argument("--region")
    b.add_argument("--zusatz")
    b.add_argument("--anzahl", type=int)
    b.add_argument("--datei", required=True)

    c = unter.add_parser("erfassen", parents=[gemeinsam],
                         help="Eine KI-Antwort im Wortlaut ablegen")
    c.add_argument("--datei", required=True)
    c.add_argument("--system", required=True,
                   help="ChatGPT, Perplexity, Google AI Overview, ...")
    c.add_argument("--frage", type=int, required=True, help="Nummer ab 1")
    c.add_argument("--antwort-datei", help="Sonst wird stdin gelesen")
    c.add_argument("--quelle", action="append",
                   help="Von der KI genannte Quelle, mehrfach moeglich")

    d = unter.add_parser("bericht", parents=[gemeinsam],
                         help="HTML-Bericht erzeugen")
    d.add_argument("--datei", help="Erhebung; ohne sie nur Teil 1")
    d.add_argument("--domain")
    d.add_argument("--firma")
    d.add_argument("--ausgabe", required=True)

    args = p.parse_args(argumente)
    als_json = args.json or "--json" in argumente

    befehle = {"pruefen": befehl_pruefen, "fragen": befehl_fragen,
               "erfassen": befehl_erfassen, "bericht": befehl_bericht}
    try:
        ergebnis = befehle[args.befehl](args)
    except (ValueError, OSError, KeyError) as e:
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
