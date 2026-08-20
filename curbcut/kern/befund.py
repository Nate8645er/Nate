#!/usr/bin/env python3
"""
befund.py - was ein gefundener Fehler ist.

Ein Befund ohne Zeilennummer ist eine Meinung. Ein Befund mit Zeilennummer
ist eine Reparaturanweisung. Der Unterschied entscheidet, ob ein Haendler
das Werkzeug behaelt oder nach zwei Wochen deinstalliert.

Darum traegt jeder Befund vier Dinge, und keines davon ist optional:
  wo   - Datei und Zeile, damit man hingehen kann
  was  - was dort steht, woertlich, damit man es wiedererkennt
  warum- welches Kriterium verletzt ist, mit seiner Nummer
  wie  - der Vorschlag, wie es aussehen muesste
"""

from dataclasses import dataclass, field

# Die sechs. Quelle: WebAIM Million 2026, eine Auswertung der Startseiten
# der Top 1'000'000 Domains. 95,9 Prozent fielen durch. Diese sechs
# Fehlertypen machen zusammen rund 96 Prozent aller gefundenen Fehler aus.
# Die Prozentzahl dahinter ist der Anteil der Seiten mit diesem Fehler.
DIE_SECHS = {
    "kontrast":  ("Zu wenig Kontrast",              83.9, "1.4.3"),
    "alt":       ("Bild ohne Alternativtext",       53.1, "1.1.1"),
    "label":     ("Eingabefeld ohne Beschriftung",  51.0, "3.3.2"),
    "leerlink":  ("Link ohne erkennbaren Text",     46.3, "2.4.4"),
    "leerknopf": ("Schaltflaeche ohne Text",        30.6, "4.1.2"),
    "sprache":   ("Seite ohne Sprachangabe",        13.5, "3.1.1"),
}

# Wie schwer wiegt ein Fehler. Nicht erfunden - abgeleitet daraus, was
# eine Pruefstelle oder ein Klaeger tatsaechlich beanstandet.
#   sperrend  - ein Mensch kommt hier nicht weiter. Kaufabbruch.
#   ernst     - benutzbar, aber nachweislich ein Verstoss.
#   hinweis   - sollte weg, traegt aber selten eine Beanstandung.
GEWICHT = {"sperrend": 3, "ernst": 2, "hinweis": 1}


@dataclass
class Befund:
    art: str            # Schluessel aus DIE_SECHS
    datei: str
    zeile: int
    stelle: str         # was dort woertlich steht
    schwere: str        # sperrend | ernst | hinweis
    vorschlag: str = ""
    sicher: bool = False   # kann automatisch repariert werden
    notiz: str = ""

    @property
    def titel(self):
        return DIE_SECHS[self.art][0]

    @property
    def kriterium(self):
        return DIE_SECHS[self.art][2]

    def __str__(self):
        marke = "auto" if self.sicher else "hand"
        return (f"{self.datei}:{self.zeile}  [{self.schwere}/{marke}]  "
                f"{self.titel} (WCAG {self.kriterium})\n"
                f"    gefunden: {self.stelle[:110]}\n"
                f"    noetig:   {self.vorschlag}")


@dataclass
class Bericht:
    shop: str = ""
    befunde: list = field(default_factory=list)
    gepruefte_dateien: int = 0
    gepruefte_zeilen: int = 0

    def dazu(self, b):
        self.befunde.append(b)

    def nach_art(self):
        d = {}
        for b in self.befunde:
            d.setdefault(b.art, []).append(b)
        return d

    def punktzahl(self):
        """0 bis 100. Nicht geschoent: eine sperrende Sache zieht dreifach.

        Das ist bewusst KEINE Prozentangabe erfuellter Kriterien. So eine
        Zahl verleitet dazu, 71 Prozent fuer gut genug zu halten - genau
        das Argument, mit dem Carrefour im Mai 2026 vor einem franzoesischen
        Gericht durchgefallen ist. Der Richter sagte sinngemaess: ein Shop
        kann nicht ein bisschen zugaenglich sein.
        """
        if not self.gepruefte_zeilen:
            return 0
        strafe = sum(GEWICHT[b.schwere] for b in self.befunde)
        # Bezug ist die Groesse des Themes: 1 Strafpunkt je 40 Zeilen
        # ist die Grenze, ab der es unbenutzbar wird.
        grenze = max(1, self.gepruefte_zeilen / 40)
        return max(0, round(100 * (1 - min(1.0, strafe / grenze))))

    def reparierbar(self):
        return [b for b in self.befunde if b.sicher]

    def handarbeit(self):
        return [b for b in self.befunde if not b.sicher]
