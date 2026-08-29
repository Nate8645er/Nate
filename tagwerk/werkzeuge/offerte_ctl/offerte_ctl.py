#!/usr/bin/env python3
# offerte_ctl - Offerten aus einer Vorlage erzeugen.
#
# Gebaut nach der cli-anything-Methodik (HKUDS, Apache 2.0):
#
#   Phase 1  Backend-Engine gefunden: LibreOffice headless. Datenmodell:
#            ODT als ZIP mit content.xml. Vorhandenes CLI als Baustein:
#            soffice --convert-to.
#   Phase 2  Unterbefehle statt REPL - eine Offerte wird einmal erzeugt,
#            nicht interaktiv bearbeitet. Maschinenlesbare Ausgabe ueber
#            --json. Befehlsgruppen: pruefen, vorlage, erstellen.
#   Phase 3  Datenschicht zuerst (vorlage.py), dann ein Probe-Befehl
#            (felder), dann der veraendernde Befehl (erstellen), zuletzt
#            die Backend-Anbindung (backend.py).
#
# Ohne LibreOffice entsteht trotzdem die ODT - nur die PDF fehlt dann.
# Das wird gemeldet, nicht verschwiegen.
#
#   python3 offerte_ctl.py pruefen
#   python3 offerte_ctl.py vorlage-neu offerte-vorlage.odt
#   python3 offerte_ctl.py felder offerte-vorlage.odt
#   python3 offerte_ctl.py erstellen offerte-vorlage.odt daten.json

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import backend  # noqa: E402
import vorlage  # noqa: E402

# Eine Schweizer Offerte im Handwerk. Bewusst schlicht - der Betrieb
# ersetzt sie spaeter durch sein eigenes Briefpapier, die Platzhalter
# bleiben dieselben.
STANDARDVORLAGE = [
    ("{{firma}}", "Titel"),
    "{{firma_adresse}}",
    "",
    "{{kunde}}",
    "{{kunde_adresse}}",
    "",
    ("Offerte {{nummer}}", "Fett"),
    "{{ort}}, {{datum}}",
    "",
    "{{einleitung}}",
    "",
    ("Leistungen", "Fett"),
    ("{{positionen}}", "Positionen"),
    "",
    ("Total exkl. MwSt: CHF {{total}}", "Fett"),
    "MwSt {{mwst_satz}}%: CHF {{mwst_betrag}}",
    ("Total inkl. MwSt: CHF {{total_brutto}}", "Fett"),
    "",
    "Diese Offerte ist gueltig bis {{gueltig_bis}}.",
    "",
    "Freundliche Gruesse",
    "{{unterschrift}}",
]

# Wird als {{positionen}} eingesetzt: eine Zeile je Leistung. Die Tabs
# treffen die Tabulatoren des Absatzstils "Positionen" - Menge links,
# Bezeichnung eingerueckt, Betrag rechtsbuendig. Mit Leerzeichen statt
# Tabs stuenden die Betraege krumm untereinander, weil ODF mehrfache
# Leerzeichen zu einem zusammenzieht.
POSITION_FORMAT = "%(menge)s %(einheit)s\t%(bezeichnung)s\tCHF %(preis)s"


def positionen_rendern(positionen):
    """Positionsliste in Textzeilen umwandeln.

    Platzhalter koennen keine Tabellen wiederholen - deshalb wird die
    Liste hier zu Text. Fuer eine Handwerker-Offerte mit drei bis zehn
    Zeilen reicht das; wer echte Tabellen braucht, ersetzt spaeter die
    Datenschicht, nicht dieses Werkzeug.
    """
    zeilen = []
    for p in positionen:
        zeilen.append(POSITION_FORMAT % {
            "menge": p.get("menge", ""),
            "einheit": p.get("einheit", ""),
            "bezeichnung": p.get("bezeichnung", ""),
            "preis": _betrag(p.get("preis", 0)),
        })
    return "\n".join(zeilen)


def _betrag(wert):
    try:
        return "%.2f" % float(wert)
    except (TypeError, ValueError):
        return str(wert)


def werte_aufbereiten(daten):
    """Rohdaten zu Platzhalterwerten machen und Summen selbst rechnen.

    Summen werden NICHT aus der Eingabedatei uebernommen, sondern aus den
    Positionen berechnet. Eine Offerte, in der die Zeilen nicht zum Total
    passen, ist ein Streit mit dem Kunden.
    """
    werte = {k: v for k, v in daten.items() if k != "positionen"}
    positionen = daten.get("positionen", [])
    werte["positionen"] = positionen_rendern(positionen)

    total = sum(float(p.get("preis", 0)) for p in positionen)
    satz = float(daten.get("mwst_satz", 8.1))
    mwst = round(total * satz / 100, 2)

    werte["total"] = _betrag(total)
    werte["mwst_satz"] = ("%g" % satz)
    werte["mwst_betrag"] = _betrag(mwst)
    werte["total_brutto"] = _betrag(total + mwst)
    return werte


# ------------------------------------------------------------- Befehle

def befehl_pruefen(args):
    """Probe-Befehl: Ist das Backend einsatzbereit?"""
    da = backend.verfuegbar()
    return {
        "libreoffice": da,
        "version": backend.version() if da else None,
        "pdf_moeglich": da,
        "hinweis": None if da else
        "Ohne LibreOffice entsteht nur die ODT-Datei, keine PDF.",
    }


def befehl_vorlage_neu(args):
    vorlage.vorlage_erzeugen(args.ziel, STANDARDVORLAGE)
    return {"erzeugt": args.ziel,
            "felder": vorlage.felder_finden(args.ziel)}


def befehl_felder(args):
    return {"vorlage": args.vorlage,
            "felder": vorlage.felder_finden(args.vorlage)}


def befehl_erstellen(args):
    with open(args.daten, encoding="utf-8") as f:
        daten = json.load(f)
    werte = werte_aufbereiten(daten)

    basis = args.name or "offerte-%s" % daten.get("nummer", "ohne-nummer")
    os.makedirs(args.ausgabe, exist_ok=True)
    odt = os.path.join(args.ausgabe, basis + ".odt")

    ergebnis = vorlage.fuellen(args.vorlage, odt, werte,
                               streng=not args.locker)
    antwort = {"odt": odt, "ersetzt": ergebnis["ersetzt"],
               "offen": ergebnis["offen"], "pdf": None, "warnung": None}

    if args.nur_odt:
        return antwort
    try:
        antwort["pdf"] = backend.nach_pdf(odt, args.ausgabe)
    except backend.BackendFehler as e:
        # Die ODT ist fertig - das wird nicht durch einen fehlenden
        # PDF-Wandler entwertet.
        antwort["warnung"] = str(e)
    return antwort


def ausgeben(daten, als_json):
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
        return
    for schluessel, wert in daten.items():
        if wert is None or wert == [] or wert == "":
            continue
        if isinstance(wert, list):
            print("%-14s %s" % (schluessel + ":", ", ".join(map(str, wert))))
        else:
            print("%-14s %s" % (schluessel + ":", wert))


def main(argumente):
    # --json muss vor UND nach dem Unterbefehl funktionieren. Alle tippen
    # es hinten ("erstellen ... --json"); nur vorne erlaubt waere ein
    # Stolperstein, den man einmal pro Tag neu entdeckt.
    gemeinsam = argparse.ArgumentParser(add_help=False)
    gemeinsam.add_argument("--json", action="store_true",
                           help="Maschinenlesbare Ausgabe")

    p = argparse.ArgumentParser(
        prog="offerte_ctl", parents=[gemeinsam],
        description="Offerten aus einer ODT-Vorlage erzeugen.")
    unter = p.add_subparsers(dest="befehl", required=True)

    unter.add_parser("pruefen", parents=[gemeinsam],
                     help="Ist LibreOffice einsatzbereit?")

    a = unter.add_parser("vorlage-neu", parents=[gemeinsam],
                         help="Standardvorlage anlegen")
    a.add_argument("ziel")

    b = unter.add_parser("felder", parents=[gemeinsam],
                         help="Platzhalter einer Vorlage zeigen")
    b.add_argument("vorlage")

    c = unter.add_parser("erstellen", parents=[gemeinsam],
                         help="Offerte aus Vorlage und Daten")
    c.add_argument("vorlage")
    c.add_argument("daten", help="JSON-Datei mit den Angaben")
    c.add_argument("--ausgabe", default=".", help="Zielordner")
    c.add_argument("--name", help="Dateiname ohne Endung")
    c.add_argument("--nur-odt", action="store_true",
                   help="Keine PDF erzeugen")
    c.add_argument("--locker", action="store_true",
                   help="Fehlende Werte erlauben (Platzhalter bleibt stehen)")

    args = p.parse_args(argumente)

    # argparse-Falle: Steht --json vor dem Unterbefehl, ueberschreibt der
    # Unterbefehl den Wert anschliessend mit seinem Vorgabewert False.
    # Deshalb zusaetzlich die Rohargumente pruefen - sonst funktioniert
    # die Kurzform nur in einer der beiden Stellungen, und zwar
    # stillschweigend.
    als_json = args.json or "--json" in argumente

    befehle = {"pruefen": befehl_pruefen, "vorlage-neu": befehl_vorlage_neu,
               "felder": befehl_felder, "erstellen": befehl_erstellen}

    try:
        ergebnis = befehle[args.befehl](args)
    except (vorlage.VorlagenFehler, backend.BackendFehler) as e:
        if als_json:
            print(json.dumps({"fehler": str(e)}, ensure_ascii=False))
        else:
            print("Fehler: %s" % e, file=sys.stderr)
        return 1
    except (OSError, ValueError) as e:
        if als_json:
            print(json.dumps({"fehler": str(e)}, ensure_ascii=False))
        else:
            print("Fehler: %s" % e, file=sys.stderr)
        return 1

    ausgeben(ergebnis, als_json)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
