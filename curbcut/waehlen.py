#!/usr/bin/env python3
"""
waehlen.py - das Raster, mit dem eine Idee gewaehlt wird.

Warum es das gibt:
Nate hat zwei Geschaefte gestartet, beide bei null Umsatz. Beide wurden
nach Gefuehl gewaehlt. Diesmal wird gerechnet - und zwar VOR dem Bauen,
damit die Zahl die Entscheidung traegt und nicht die Begeisterung.

Die Gewichte sind keine Meinung, sie kommen aus dem, was bei Nate
nachweislich schiefging:

  Erster Franken       Zwei Anlaeufe, null Umsatz. Nichts ist wichtiger
                       als ein Modell, das frueh Geld sieht.
  Vertrieb ohne Netz   Genau hier sind beide gescheitert. Ein Modell,
                       das Kaltakquise braucht, ist fuer ihn wertlos,
                       egal wie gut es sonst aussieht.
  Burggraben           Ein Wrapper, der 2027 weg ist, hilft nicht.
  Kapitalbedarf        Er hatte CHF 12. Das ist die Obergrenze, nicht
                       eine Startbedingung, die man wegdiskutiert.

Alles wird von 0 bis 10 bewertet. Wer bei einem K.-o.-Kriterium unter
der Schwelle liegt, fliegt raus - auch mit hoher Gesamtpunktzahl.
Sonst gewinnt am Ende wieder die schoenste Idee statt der tragfaehigen.
"""

from dataclasses import dataclass, field

# name, gewicht, was eine 10 bedeutet
KRITERIEN = [
    ("erster_franken",   3.0, "zahlender Kunde in unter 30 Tagen realistisch"),
    ("vertrieb_ohne_netz", 3.0, "Kunden finden das Produkt selbst, ohne dass Nate verkauft"),
    ("automatisierbar",  2.5, "laeuft ohne taegliche Menschenarbeit"),
    ("wiederkehrend",    2.5, "Abo, nicht Einzelverkauf"),
    ("burggraben",       2.5, "wird von OpenAI/Google nicht in einem Update weggefegt"),
    ("marge",            2.0, "Bruttomarge ueber 80 Prozent"),
    ("marktgroesse",     2.0, "weltweit, Millionen moegliche Zahler"),
    ("zahlungsbereit",   2.0, "der Kaeufer hat ein Budget und einen Grund, JETZT zu zahlen"),
    ("kapitalbedarf",    2.0, "Start unter CHF 100"),
    ("skalierung",       1.5, "der tausendste Kunde kostet fast nichts mehr"),
    ("dauerhaft",        1.5, "auch 2030 noch ein Geschaeft"),
    ("nate_kann_es",     1.5, "kein Fachwissen noetig, das Nate nicht hat und nicht kaufen kann"),
]

# Wer hier durchfaellt, ist raus. Ohne Diskussion.
KO = {
    "erster_franken": 5,
    "vertrieb_ohne_netz": 5,
    "kapitalbedarf": 6,
    "burggraben": 4,
}


@dataclass
class Idee:
    name: str
    werte: dict
    notiz: str = ""
    raus: list = field(default_factory=list)

    def punkte(self):
        summe = gewicht = 0.0
        for kriterium, g, _ in KRITERIEN:
            summe += self.werte.get(kriterium, 0) * g
            gewicht += g
        return summe / gewicht

    def pruefen(self):
        self.raus = [
            f"{k} = {self.werte.get(k, 0)} (mindestens {schwelle})"
            for k, schwelle in KO.items()
            if self.werte.get(k, 0) < schwelle
        ]
        return not self.raus


def tabelle(ideen):
    ideen = sorted(ideen, key=lambda i: (i.pruefen(), i.punkte()), reverse=True)
    breite = max(len(i.name) for i in ideen) + 2
    zeilen = []
    zeilen.append(f"{'IDEE':<{breite}} {'PUNKTE':>7}  STATUS")
    zeilen.append("-" * (breite + 40))
    for i in ideen:
        ok = i.pruefen()
        status = "im Rennen" if ok else "RAUS: " + "; ".join(i.raus)
        zeilen.append(f"{i.name:<{breite}} {i.punkte()*10:>6.1f}  {status}")
    return "\n".join(zeilen)


if __name__ == "__main__":
    print("Dieses Modul wird von der Auswahl importiert.")
    print(f"{len(KRITERIEN)} Kriterien, {len(KO)} K.-o.-Schwellen.")
