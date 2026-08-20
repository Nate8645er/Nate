#!/usr/bin/env python3
"""
regeln.py - die sechs Fehler, die 96 Prozent ausmachen.

Quelle der Auswahl: WebAIM Million 2026, eine maschinelle Auswertung der
Startseiten der eine Million meistbesuchten Domains. 95,9 Prozent fielen
durch. Sechs Fehlertypen machen zusammen rund 96 Prozent aller gefundenen
Verstoesse aus.

Das ist die ganze Begruendung fuer den Zuschnitt dieses Werkzeugs. Es
prueft nicht alle 87 Kriterien von WCAG 2.2 - es prueft die sechs, an
denen fast alles haengt, und es prueft sie richtig. Ein Werkzeug, das
fuenfzig Kriterien halb prueft, erzeugt eine Liste, die niemand abarbeitet.

DIE REGEL HINTER DEN REGELN

Im Zweifel wird nichts gemeldet. Jeder Fehlalarm kostet mehr Vertrauen,
als ein uebersehener Fehler kostet: Wer zehn falsche Befunde sieht, glaubt
auch dem elften nicht, der echt ist - und dann nuetzt die ganze Pruefung
nichts mehr.
"""

import re

import farbe
from befund import Befund
from seite import attribute, hat_text, paare, stilregeln, _groesse

# Eingabearten, die eine sichtbare Beschriftung brauchen.
BRAUCHT_LABEL = {"text", "email", "password", "search", "tel", "url",
                 "number", "date", "datetime-local", "month", "week",
                 "time", "checkbox", "radio", "file", "range", "color"}


def sprache(s, bericht):
    """3.1.1 - ohne Sprachangabe liest die Vorlesesoftware falsch vor."""
    m = re.search(r"<html\b([^>]*)>", s.arbeit, re.IGNORECASE)
    if not m:
        return
    a = attribute(m.group(1))
    wert = a.get("lang", "").strip()
    if not wert:
        bericht.dazu(Befund(
            art="sprache", datei=s.url or "seite", zeile=s.zeile(m.start()),
            stelle=s.zitat(m.start(), m.end()), schwere="ernst", sicher=True,
            vorschlag='lang="de" in das <html>-Element setzen (oder die '
                      'Sprache, in der die Seite geschrieben ist). Ohne die '
                      'Angabe liest eine Vorlesesoftware deutschen Text mit '
                      'englischer Aussprache vor - unverstaendlich.',
        ))
    elif not re.match(r"^[a-z]{2,3}(-[A-Za-z0-9]+)*$", wert):
        bericht.dazu(Befund(
            art="sprache", datei=s.url or "seite", zeile=s.zeile(m.start()),
            stelle=s.zitat(m.start(), m.end()), schwere="hinweis", sicher=True,
            vorschlag=f'lang="{wert}" ist kein gueltiges Sprachkuerzel. '
                      f'Erwartet wird etwas wie de, de-CH oder en.',
        ))


def bilder(s, bericht):
    """1.1.1 - ein Bild ohne Alternativtext existiert fuer Blinde nicht."""
    for m in re.finditer(r"<img\b([^>]*?)/?>", s.arbeit, re.IGNORECASE | re.DOTALL):
        a = attribute(m.group(1))
        z = s.zeile(m.start())

        # Ein Bild, das ausdruecklich versteckt ist, zaehlt nicht.
        if a.get("aria-hidden") == "true" or a.get("role") == "presentation":
            continue

        if "alt" not in a:
            quelle = a.get("src", "")[:60]
            bericht.dazu(Befund(
                art="alt", datei=s.url or "seite", zeile=z,
                stelle=s.zitat(m.start(), m.end()),
                schwere="ernst", sicher=True,
                vorschlag='alt="..." ergaenzen: beschreibe, was zu sehen ist '
                          'und warum es hier steht. Nicht "Bild" und nicht '
                          'den Dateinamen. Wenn das Bild reine Dekoration '
                          'ist, gehoert alt="" hin - leer, aber vorhanden.',
                notiz=quelle,
            ))
            continue

        wert = a["alt"].strip()
        if not wert:
            continue     # leeres alt ist die richtige Angabe fuer Deko

        # Ein Alternativtext, der den Dateinamen wiederholt, hilft niemandem.
        datei = a.get("src", "").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if datei and wert.lower() in (datei.lower(),
                                      datei.lower().replace("-", " "),
                                      datei.lower().replace("_", " ")):
            bericht.dazu(Befund(
                art="alt", datei=s.url or "seite", zeile=z,
                stelle=s.zitat(m.start(), m.end()),
                schwere="hinweis", sicher=False,
                vorschlag=f'Der Alternativtext ist der Dateiname. Vorgelesen '
                          f'klingt das wie "{wert}" - das beschreibt nichts.',
            ))
        elif re.match(r"^(bild|image|foto|photo|grafik|icon|logo)\W*\d*$",
                      wert, re.IGNORECASE):
            bericht.dazu(Befund(
                art="alt", datei=s.url or "seite", zeile=z,
                stelle=s.zitat(m.start(), m.end()),
                schwere="hinweis", sicher=False,
                vorschlag=f'"{wert}" sagt nur, DASS dort etwas ist, nicht WAS. '
                          f'Eine Vorlesesoftware kuendigt Bilder ohnehin an.',
            ))


def bedienelemente(s, bericht):
    """2.4.4 und 4.1.2 - ein Knopf ohne Namen ist nicht bedienbar."""
    for tag, art, wort in (("a", "leerlink", "Link"),
                           ("button", "leerknopf", "Schaltflaeche")):
        for m, inhalt in paare(s.arbeit, tag):
            a = attribute(m.group(1))

            if tag == "a" and "href" not in a:
                continue          # Anker ohne Ziel ist kein Link
            if a.get("aria-hidden") == "true":
                continue
            if hat_text(inhalt):
                continue
            if any(a.get(x, "").strip() for x in
                   ("aria-label", "aria-labelledby", "title")):
                continue

            # Bild mit Alternativtext im Inneren zaehlt als Name.
            bild = re.search(r"<img\b([^>]*?)/?>", inhalt, re.IGNORECASE)
            if bild and attribute(bild.group(1)).get("alt", "").strip():
                continue
            # <svg> mit <title> ebenso.
            if re.search(r"<title\b[^>]*>\s*\S", inhalt, re.IGNORECASE):
                continue

            innen = re.sub(r"\s+", " ", inhalt).strip()[:40]
            was = "ein Symbol" if "<svg" in inhalt.lower() else (
                  "ein Bild" if "<img" in inhalt.lower() else "nichts")
            bericht.dazu(Befund(
                art=art, datei=s.url or "seite", zeile=s.zeile(m.start()),
                stelle=s.zitat(m.start(), m.end() + len(inhalt) + len(tag) + 3),
                schwere="sperrend", sicher=True,
                vorschlag=f'{wort} enthaelt {was} und keinen vorlesbaren Namen. '
                          f'aria-label="..." ergaenzen und darin sagen, was '
                          f'PASSIERT, nicht wie es aussieht: also '
                          f'"Warenkorb oeffnen", nicht "Taschensymbol".',
                notiz=innen,
            ))


def formulare(s, bericht):
    """3.3.2 - ein Feld ohne Beschriftung wird blind ausgefuellt."""
    t = s.arbeit

    fuer = {attribute(m.group(1)).get("for", "").strip()
            for m in re.finditer(r"<label\b([^>]*)>", t, re.IGNORECASE)}
    fuer.discard("")

    umschlossen = set()
    for m, inhalt in paare(t, "label"):
        versatz = m.end()
        for n in re.finditer(r"<(input|select|textarea)\b", inhalt, re.IGNORECASE):
            umschlossen.add(versatz + n.start())

    for tag in ("input", "select", "textarea"):
        for m in re.finditer(rf"<{tag}\b([^>]*?)/?>", t, re.IGNORECASE | re.DOTALL):
            a = attribute(m.group(1))
            typ = a.get("type", "text").lower()

            if tag == "input" and typ not in BRAUCHT_LABEL:
                continue      # submit, hidden, button brauchen kein Label
            if a.get("aria-hidden") == "true":
                continue
            if any(a.get(x, "").strip() for x in
                   ("aria-label", "aria-labelledby", "title")):
                continue
            kennung = a.get("id", "").strip()
            if kennung and kennung in fuer:
                continue
            if m.start() in umschlossen:
                continue

            platzhalter = a.get("placeholder", "").strip()
            if platzhalter:
                warum = (f'Der Platzhalter "{platzhalter}" ist keine '
                         f'Beschriftung. Er verschwindet, sobald jemand '
                         f'tippt - wer dann unterbrochen wird, weiss nicht '
                         f'mehr, was in das Feld gehoert. '
                         f'<label for="ID"> ergaenzen.')
            else:
                warum = ('Feld ohne Beschriftung. <label for="ID">Text</label> '
                         'ergaenzen, oder aria-label setzen, wenn an dieser '
                         'Stelle kein sichtbarer Text passt.')

            bericht.dazu(Befund(
                art="label", datei=s.url or "seite", zeile=s.zeile(m.start()),
                stelle=s.zitat(m.start(), m.end()),
                schwere="sperrend", sicher=bool(kennung),
                vorschlag=warum,
                notiz=a.get("name", ""),
            ))


# ----------------------------------------------------------------- Kontrast

def _paare_aus_stil(text):
    """Findet (vorne, hinten) in einem Stil-Block, wenn BEIDE dastehen."""
    e = {}
    for stueck in text.split(";"):
        if ":" in stueck:
            k, _, v = stueck.partition(":")
            e[k.strip().lower()] = v.strip()
    vorne = farbe.lesen(e.get("color"))
    hinten = None
    for schluessel in ("background-color", "background"):
        if schluessel in e:
            # background kann ein ganzer Kurzbefehl sein - nur die Farbe
            m = re.search(r"(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|[a-z]+)",
                          e[schluessel])
            if m:
                hinten = farbe.lesen(m.group(1))
                if hinten:
                    break
    return vorne, hinten, e


def kontrast(s, bericht):
    """1.4.3 - der haeufigste Fehler im Web, auf 83,9 Prozent aller Seiten.

    Gemeldet wird nur, wo Vorder- UND Hintergrundfarbe am selben Ort
    stehen. Alles andere braeuchte die vollstaendige Kaskade und damit
    einen Browser. Was hier nicht sicher zugeordnet werden kann, bleibt
    ungemeldet - siehe die Regel hinter den Regeln oben.
    """
    gesehen = set()

    # 1. Inline: <p style="color:#999; background:#fff">
    for m in re.finditer(r"""<(\w+)\b[^>]*\bstyle\s*=\s*["']([^"']+)["'][^>]*>""",
                         s.arbeit, re.IGNORECASE):
        vorne, hinten, e = _paare_aus_stil(m.group(2))
        if not (vorne and hinten):
            continue
        px = _groesse(e.get("font-size"))
        fett = e.get("font-weight", "") in ("bold", "bolder", "600", "700",
                                            "800", "900")
        _melden(s, bericht, vorne, hinten, px, fett,
                m.start(), m.end(), f"<{m.group(1)} style=...>", gesehen)

    # 2. Stilblock: Selektoren, die beide Farben setzen
    for block in s.stile:
        for sel, e in stilregeln(block).items():
            if "color" not in e:
                continue
            roh = e.get("background-color") or e.get("background")
            if not roh:
                continue
            mm = re.search(r"(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|[a-z]+)", roh)
            vorne = farbe.lesen(e["color"])
            hinten = farbe.lesen(mm.group(1)) if mm else None
            if not (vorne and hinten):
                continue
            px = _groesse(e.get("font-size"))
            fett = e.get("font-weight", "") in ("bold", "bolder", "600", "700",
                                                "800", "900")
            # Der Selektor steht in einer Stildatei, nicht im HTML.
            # find() liefert dann -1, und aus -1 wurde bisher "Zeile 1"
            # samt einem Zitat von <!doctype html> - ein Ort, an dem
            # nichts davon steht. Lieber gar keine Zeile nennen als
            # eine falsche.
            pos = s.original.find(sel) if len(sel) > 3 else -1
            _melden(s, bericht, vorne, hinten, px, fett,
                    max(0, pos), max(0, pos) + len(sel), sel, gesehen,
                    aus_datei=(pos < 0))


def _melden(s, bericht, vorne, hinten, px, fett, start, ende, wo, gesehen,
            aus_datei=False):
    ziel = farbe.ziel_fuer(px, fett)
    wert = farbe.kontrast(vorne, hinten)
    if wert is None or wert >= ziel:
        return

    # Exakt gleiche Farbe vorne wie hinten: fast immer ein Artefakt der
    # flachen CSS-Auswertung, nicht unsichtbarer Text. Etwa wenn eine
    # Regel eine Variable definiert und derselbe Wert in beiden
    # Eigenschaften landet, obwohl er nie zusammen gerendert wird.
    #
    # Gefunden an Nates eigenem Laden: gemeldet wurde "#111111 auf
    # #111111 ergibt 1.00 zu 1", samt dem Rat, die Schrift heller zu
    # setzen. Auf der Seite war nichts unsichtbar. Ein solcher Befund
    # kostet mehr Vertrauen, als zehn richtige einbringen.
    if vorne[:3] == hinten[:3]:
        return

    schluessel = (farbe.als_hex(vorne), farbe.als_hex(hinten), round(ziel, 1))
    if schluessel in gesehen:
        return       # dieselbe Farbkombination nicht dreissigmal melden
    gesehen.add(schluessel)

    rat = farbe.vorschlag(vorne, hinten, ziel)
    grund = (f"{farbe.als_hex(vorne)} auf {farbe.als_hex(hinten)} ergibt "
             f"{wert:.2f} zu 1. Noetig sind {ziel} zu 1"
             + (f" (Schrift ist {px:.0f}px" + (", fett)" if fett else ")")
                if px else "") + ". ")
    bericht.dazu(Befund(
        art="kontrast",
        datei=s.url or "seite",
        zeile=0 if aus_datei else s.zeile(start),
        stelle=(f"Stilregel  {wo} {{ ... }}" if aus_datei
                else s.zitat(start, ende)),
        schwere="ernst",
        sicher=bool(rat and rat[1]),
        vorschlag=grund + (rat[2] if rat else ""),
        notiz=wo,
    ))


ALLE = (sprache, bilder, bedienelemente, formulare, kontrast)
