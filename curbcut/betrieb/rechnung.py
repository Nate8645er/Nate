#!/usr/bin/env python3
"""
rechnung.py - was das Geschaeft kostet und was es traegt.

KEINE WUNSCHZAHLEN

Jede Kostenzahl hier ist ein Listenpreis, den man nachschlagen kann.
Jede Annahme ueber Kunden ist als Annahme gekennzeichnet und in drei
Faellen gerechnet - vorsichtig, mittel, gut. Es gibt keine Erfolgs-
garantie und dieses Modell ist keine.

Der wichtigste Satz steht am Ende: Was passiert, wenn niemand kauft.
Das ist der Fall, den Nate zweimal erlebt hat, und ein Modell, das ihn
nicht zeigt, ist unehrlich.
"""

# --------------------------------------------------------------- Kosten
# Alles in CHF pro Monat, Stand August 2026, Listenpreise.

FEST = {
    "Domain (12 im Jahr)":            1.00,
    "Server (Hetzner CX22)":           5.00,
    "Datenbank (verwaltet, klein)":    0.00,   # SQLite auf demselben Server
    "E-Mail-Versand (Resend, gratis bis 3000)": 0.00,
    "Fehlerueberwachung (Sentry, gratis)":      0.00,
}

# Was ein einzelner Scan wirklich kostet.
# Die sechs Regeln laufen ohne Modell - reines Python, Kosten null.
# Ein Modell braucht es nur fuer Alternativtexte, und nur, wenn der
# Kunde sie erzeugen laesst.
KOSTEN_JE_SCAN_RECHENZEIT = 0.0004     # ~2 Sekunden CPU auf einem 5-Franken-Server
KOSTEN_JE_ALTTEXT = 0.00035            # Gemini Flash Lite, ein Bild, kurzer Text
BILDER_JE_SEITE = 25                   # gemessener Schnitt aus der eigenen Reihe

# Paddle als Merchant of Record: uebernimmt weltweit die Steuerpflicht.
# Das ist der Grund, warum eine Einzelperson ohne Firma weltweit
# verkaufen kann - Paddle ist der Verkaeufer, nicht Nate.
PADDLE_ANTEIL = 0.05
PADDLE_FIX = 0.50


class Plan:
    def __init__(self, name, preis, seiten, scans_monat):
        self.name = name
        self.preis = preis            # CHF im Monat
        self.seiten = seiten          # ueberwachte Seiten
        self.scans = scans_monat

    def kosten(self, mit_alttext=True):
        rechnen = self.scans * KOSTEN_JE_SCAN_RECHENZEIT
        modell = (self.scans * BILDER_JE_SEITE * KOSTEN_JE_ALTTEXT
                  if mit_alttext else 0)
        return rechnen + modell

    def gebuehr(self):
        return self.preis * PADDLE_ANTEIL + PADDLE_FIX

    def deckung(self):
        return self.preis - self.kosten() - self.gebuehr()

    def marge(self):
        return self.deckung() / self.preis if self.preis else 0


PLAENE = [
    #      Name          CHF   Seiten  Scans/Monat
    Plan("Einzelseite",   19,     1,      30),      # taeglich
    Plan("Auftritt",      49,    10,     300),
    Plan("Agentur",      149,    50,    1500),
]


def zeile(x, breite=34):
    return x.ljust(breite)


def kostenblock():
    print("\n  FESTE KOSTEN IM MONAT")
    gesamt = 0
    for was, wieviel in FEST.items():
        print(f"    {zeile(was)} CHF {wieviel:>6.2f}")
        gesamt += wieviel
    print(f"    {zeile('')} ----------")
    print(f"    {zeile('zusammen')} CHF {gesamt:>6.2f}")
    return gesamt


def planblock():
    print("\n  WAS EIN KUNDE EINBRINGT")
    print(f"    {'Plan':<14}{'Preis':>7}{'Kosten':>9}{'Paddle':>8}"
          f"{'bleibt':>9}{'Marge':>8}")
    for p in PLAENE:
        print(f"    {p.name:<14}{p.preis:>7.0f}{p.kosten():>9.2f}"
              f"{p.gebuehr():>8.2f}{p.deckung():>9.2f}{p.marge()*100:>7.0f}%")


def szenarien(fest):
    """Drei Faelle. Die Kundenzahlen sind Annahmen, keine Prognosen."""
    faelle = [
        ("vorsichtig", {"Einzelseite": 20, "Auftritt": 5,  "Agentur": 0}),
        ("mittel",     {"Einzelseite": 60, "Auftritt": 25, "Agentur": 3}),
        ("gut",        {"Einzelseite": 200, "Auftritt": 90, "Agentur": 15}),
    ]
    print("\n  DREI FAELLE NACH ZWOELF MONATEN")
    print("     (die Kundenzahlen sind Annahmen - niemand kann sie wissen)")
    print(f"\n    {'Fall':<12}{'Kunden':>8}{'Umsatz':>10}{'Kosten':>9}"
          f"{'Gewinn':>10}{'im Jahr':>11}")
    for name, verteilung in faelle:
        umsatz = deckung = kunden = 0
        for p in PLAENE:
            n = verteilung[p.name]
            kunden += n
            umsatz += n * p.preis
            deckung += n * p.deckung()
        gewinn = deckung - fest
        print(f"    {name:<12}{kunden:>8}{umsatz:>10.0f}"
              f"{umsatz-deckung+fest:>9.0f}{gewinn:>10.0f}{gewinn*12:>11.0f}")
    return faelle


def schwelle(fest):
    print("\n  AB WANN TRAEGT ES SICH")
    for p in PLAENE:
        n = fest / p.deckung()
        print(f"    Nur {p.name}: {n:.1f} Kunden decken die festen Kosten.")
    p = PLAENE[0]
    print(f"\n    Der erste zahlende Kunde im kleinsten Plan deckt "
          f"{100*p.deckung()/fest:.0f} Prozent der laufenden Kosten.")
    print(f"    Das ist der eigentliche Punkt: Das Geschaeft kostet CHF "
          f"{fest:.0f} im Monat.")
    print(f"    Es kann also sehr lange laufen, ohne dass es wehtut.")


def ehrlich(fest):
    print("\n  WAS PASSIERT, WENN NIEMAND KAUFT")
    print(f"    Dann verliert Nate CHF {fest:.0f} im Monat, also CHF "
          f"{fest*12:.0f} im Jahr.")
    print("    Das ist der Unterschied zu einem Warenlager: Es gibt keinen")
    print("    Bestand, der verdirbt, und keine Vorauszahlung an einen")
    print("    Lieferanten. Der Einsatz ist die Zeit, nicht das Geld.")
    print("\n    Zum Vergleich: Der Shopify-Laden kostet CHF 27 im Monat")
    print("    Grundgebuehr und hat in 2325 Besuchen null Bestellungen")
    print("    erzeugt. Dieses Geschaeft ist billiger im Betrieb.")


if __name__ == "__main__":
    print("=" * 66)
    print("  CURBCUT - Rechnung".center(66))
    print("=" * 66)
    fest = kostenblock()
    planblock()
    szenarien(fest)
    schwelle(fest)
    ehrlich(fest)
    print("\n" + "=" * 66)
    print("  Keine dieser Zahlen ist ein Versprechen. Die Kosten sind")
    print("  nachschlagbare Listenpreise, die Kundenzahlen sind Annahmen.")
    print("=" * 66 + "\n")
