#!/usr/bin/env python3
"""
bauteile.py - fasst zusammen, was dieselbe Ursache hat.

DAS PROBLEM, DAS DIESE DATEI LOEST

Ein Test an 20min.ch ergab 113 Befunde. Davon waren 59 derselbe Knopf:
ein Teilen-Symbol, das auf der Startseite neben jedem Artikel steht. Im
Quelltext ist das EINE Stelle. Der Betreiber muss ein einziges aria-label
ergaenzen, und 59 Befunde sind weg.

Wer ihm stattdessen eine Liste mit 113 Zeilen hinlegt, hat ihm nicht
geholfen - er hat ihn erschlagen. Genau daran scheitern die verbreiteten
Pruefwerkzeuge: Sie geben Vollstaendigkeit aus und meinen Sorgfalt, aber
niemand arbeitet eine Liste mit hunderten Eintraegen ab. Sie wird
weggeklickt, und danach ist die Seite so unzugaenglich wie vorher.

"113 Fehler" schreckt ab. "Vier Bauteile, eines davon 59 Mal eingebunden"
kann man am Donnerstagnachmittag erledigen.

WIE ERKANNT WIRD, DASS ZWEI FEHLER DERSELBE SIND

Ueber die Signatur des Bauteils: Elementart plus die Klassen, die es
traegt. Zwei <button class="teilen"> sind dasselbe Bauteil, auch wenn sie
an 59 Stellen stehen. Bei Bildern zaehlt zusaetzlich, ob sie aus derselben
Quelle kommen - ein Fotostrom aus einem Bildserver ist ein Muster, kein
Einzelfall.

Das ist eine Heuristik, keine Wahrheit. Sie kann zwei verschiedene
Bauteile zusammenwerfen, die zufaellig dieselben Klassen tragen. Der
Bericht sagt darum immer, wie viele Vorkommen zusammengefasst wurden,
und nennt die ersten Fundstellen einzeln - damit der Betreiber selbst
sieht, ob es wirklich dasselbe ist.
"""

import re
from dataclasses import dataclass, field

KLASSE = re.compile(r"""\bclass\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
TAG = re.compile(r"<(\w+)")
QUELLE = re.compile(r"""\bsrc\s*=\s*["']([^"']*)["']""", re.IGNORECASE)

# Klassen, die von Baukaesten erzeugt werden und sich bei jedem Bau
# aendern. Sie taugen nicht zur Wiedererkennung.
FLUECHTIG = re.compile(r"^(sc-[0-9a-f]{4,}|css-[0-9a-z]{4,}|jsx-\d+|"
                       r"[a-z]{1,3}[A-Za-z]{4,8}\d*)$")

# Zufallsanhaengsel an einer sonst sprechenden Klasse:
#   swiper-button-prev--R4bltkklqb6-   ->   swiper-button-prev
# Ohne das erscheint derselbe Karussellknopf fuenfmal als fuenf
# verschiedene Bauteile, und die Zahl "Stellen im Quelltext" ist gelogen.
ANHAENGSEL = re.compile(r"^(.*?)--[A-Za-z0-9]{6,}-?$")


def _kern(klasse):
    """Schneidet Zufallsanhaengsel ab, behaelt den sprechenden Teil."""
    m = ANHAENGSEL.match(klasse)
    return m.group(1) if m and len(m.group(1)) >= 3 else klasse


def signatur(befund):
    """Woran erkennt man, dass zwei Befunde dieselbe Ursache haben?"""
    roh = befund.stelle
    tag = (TAG.search(roh).group(1).lower() if TAG.search(roh) else "?")

    klassen = []
    m = KLASSE.search(roh)
    if m:
        for k in m.group(1).split():
            # Zufallsklassen aus Baukaesten wegwerfen - sie unterscheiden
            # Bauteile nicht, sie unterscheiden nur Bauvorgaenge.
            k = _kern(k)
            if not FLUECHTIG.match(k):
                klassen.append(k)

    teile = [befund.art, tag] + sorted(klassen)[:3]

    # Bilder ohne Klassen: nach Herkunft gruppieren.
    if befund.art == "alt" and not klassen:
        q = QUELLE.search(roh)
        if q:
            wirt = re.sub(r"^https?://", "", q.group(1)).split("/")[0]
            teile.append(wirt or "gleiche-quelle")

    return "|".join(teile)


@dataclass
class Bauteil:
    art: str
    signatur: str
    befunde: list = field(default_factory=list)

    @property
    def anzahl(self):
        return len(self.befunde)

    @property
    def erster(self):
        return self.befunde[0]

    @property
    def schwere(self):
        for stufe in ("sperrend", "ernst", "hinweis"):
            if any(b.schwere == stufe for b in self.befunde):
                return stufe
        return "hinweis"

    @property
    def zeilen(self):
        return sorted({b.zeile for b in self.befunde})

    def beschreiben(self):
        if self.anzahl == 1:
            if self.erster.zeile == 0:
                return "in einer Stildatei (nicht im HTML)"
            return f"an einer Stelle (Zeile {self.erster.zeile})"
        z = self.zeilen
        wo = (f"Zeile {z[0]}" if len(z) == 1
              else f"Zeilen {z[0]} bis {z[-1]}")
        return (f"{self.anzahl} Mal eingebunden, {wo} - im Quelltext "
                f"ist das eine Stelle")


def buendeln(befunde):
    """Gruppiert Befunde zu Bauteilen. Schwerste zuerst, dann haeufigste."""
    nach = {}
    for b in befunde:
        nach.setdefault(signatur(b), []).append(b)

    teile = [Bauteil(art=v[0].art, signatur=k, befunde=v)
             for k, v in nach.items()]
    rang = {"sperrend": 0, "ernst": 1, "hinweis": 2}
    teile.sort(key=lambda t: (rang[t.schwere], -t.anzahl))
    return teile


def ersparnis(befunde):
    """Wie viele Handgriffe statt wie viele Befunde?"""
    teile = buendeln(befunde)
    return len(teile), len(befunde)
