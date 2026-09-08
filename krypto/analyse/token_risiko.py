# KRYPTO - Token-Risiko und Betrugsindikatoren.
#
# Fuenf Stufen: LOW, MEDIUM, HIGH, EXTREME, UNKNOWN.
#
# UNKNOWN ist keine Verlegenheitsstufe. Sie ist die richtige Antwort,
# wenn zu wenig gemessen werden konnte - und sie ist gefaehrlicher als
# HIGH, weil sie oft aussieht wie "nichts gefunden".
#
# Was dieses Modul NICHT kann, und das ist der wichtigste Absatz der
# Datei:
#
#   Es liest keinen Vertragsquelltext. Ohne Etherscan-Schluessel gibt
#   es keinen verifizierten Quelltext, also keine Pruefung auf
#   Mint-Funktionen, Blacklists, Transfergebuehren oder Besitzrechte.
#   Es prueft keine Liquiditaetssperre. Es fuehrt keinen
#   Honeypot-Test durch (das hiesse, echtes Geld zu riskieren).
#   Es kennt die Halterverteilung nicht.
#
# Was es kann: die oeffentlich sichtbaren Zahlen von DexScreener auf
# bekannte Muster pruefen. Das faengt plumpe Faelle. Es faengt keinen
# guten Betrueger. LOW RISK heisst hier "keine der geprueften
# Auffaelligkeiten" - nicht "sicher".

STUFEN = ("LOW", "MEDIUM", "HIGH", "EXTREME", "UNKNOWN")


class Risikobefund:
    def __init__(self, stufe, punkte, funde, ungeprueft):
        self.stufe = stufe
        self.punkte = punkte           # 0..100, hoeher = schlimmer
        self.funde = funde             # (Gewicht, Text)
        self.ungeprueft = ungeprueft   # was gar nicht geprueft werden konnte

    def __repr__(self):
        return "<Risiko %s (%d)>" % (self.stufe, self.punkte)

    def bericht(self):
        zeilen = ["RISIKOSTUFE: %s  (%d/100 Risikopunkte)"
                  % (self.stufe, self.punkte)]
        if self.funde:
            zeilen.append("Gefunden:")
            zeilen += ["  [%2d] %s" % (g, t) for g, t in
                       sorted(self.funde, reverse=True)]
        else:
            zeilen.append("Gefunden: keine der geprueften Auffaelligkeiten.")
        zeilen.append("NICHT GEPRUEFT (kein Schluessel / nicht moeglich):")
        zeilen += ["  - %s" % u for u in self.ungeprueft]
        zeilen.append("Diese Pruefung ist keine Garantie gegen Betrug.")
        return "\n".join(zeilen)


# Was ohne bezahlte Quellen grundsaetzlich ungeprueft bleibt. Diese
# Liste steht in JEDEM Befund - auch bei LOW RISK. Gerade dann.
UNGEPRUEFT_IMMER = [
    "Vertragsquelltext (braucht Etherscan-Schluessel)",
    "Besitzrechte am Vertrag / Mint-Funktion",
    "Liquiditaetssperre",
    "Honeypot-Verhalten (nur mit echtem Geld testbar - wird nicht getan)",
    "Halterverteilung / Konzentration",
    "Smart-Money- und Whale-Bewegungen (braucht Nansen/Arkham)",
]


def bewerten(paar=None, liq_usd=None, volumen_24h=None, marktkapital=None,
             fdv=None, alter_tage=None, kaeufe=None, verkaeufe=None,
             aend_24h=None):
    """Risikoeinstufung aus oeffentlich sichtbaren Zahlen.

    Alle Angaben koennen aus einem dexscreener.Paar kommen oder
    einzeln uebergeben werden.
    """
    if paar is not None:
        liq_usd = liq_usd if liq_usd is not None else paar.liquiditaet
        volumen_24h = (volumen_24h if volumen_24h is not None
                       else paar.volumen_24h)
        marktkapital = (marktkapital if marktkapital is not None
                        else paar.marktkapital)
        fdv = fdv if fdv is not None else paar.fdv
        alter_tage = alter_tage if alter_tage is not None else paar.alter_tage
        kaeufe = kaeufe if kaeufe is not None else paar.kaeufe_24h
        verkaeufe = (verkaeufe if verkaeufe is not None
                     else paar.verkaeufe_24h)
        aend_24h = aend_24h if aend_24h is not None else paar.aend_24h

    funde = []
    ungeprueft = list(UNGEPRUEFT_IMMER)
    messbar = 0

    # --- Liquiditaet ---
    if liq_usd is None:
        ungeprueft.append("Liquiditaet (keine Angabe erhalten)")
    else:
        messbar += 1
        if liq_usd < 10_000:
            funde.append((40, "Liquiditaet nur %.0f USD - eine Position "
                              "laesst sich praktisch nicht aufloesen"
                          % liq_usd))
        elif liq_usd < 50_000:
            funde.append((25, "Liquiditaet %.0f USD - sehr duenn" % liq_usd))
        elif liq_usd < 250_000:
            funde.append((10, "Liquiditaet %.0f USD - duenn" % liq_usd))

    # --- Alter ---
    if alter_tage is None:
        ungeprueft.append("Alter des Handelspaares")
    else:
        messbar += 1
        if alter_tage < 1:
            funde.append((35, "Paar ist weniger als 24 Stunden alt"))
        elif alter_tage < 7:
            funde.append((20, "Paar erst %.1f Tage alt" % alter_tage))
        elif alter_tage < 30:
            funde.append((10, "Paar erst %.0f Tage alt" % alter_tage))

    # --- Umschlag: Volumen gegen Liquiditaet ---
    if liq_usd and volumen_24h is not None:
        messbar += 1
        u = volumen_24h / liq_usd if liq_usd else None
        if u is not None and u > 50:
            funde.append((30, "Volumen ist das %.0f-fache der Liquiditaet - "
                              "typisches Muster fuer Wash-Trading" % u))
        elif u is not None and u > 20:
            funde.append((15, "Volumen ist das %.0f-fache der Liquiditaet"
                          % u))
        elif u is not None and u < 0.02:
            funde.append((15, "kaum Handel (Umschlag %.3f) - Ausstieg "
                              "koennte dauern" % u))
    else:
        ungeprueft.append("Verhaeltnis Volumen zu Liquiditaet")

    # --- FDV gegen Marktkapital ---
    if fdv and marktkapital:
        messbar += 1
        v = fdv / marktkapital
        if v > 10:
            funde.append((30, "Vollverwaesserte Bewertung ist das %.0f-fache "
                              "des Marktkapitals - sehr viele Token noch "
                              "nicht im Umlauf" % v))
        elif v > 3:
            funde.append((15, "FDV %.1fx ueber Marktkapital" % v))
    else:
        ungeprueft.append("Verhaeltnis FDV zu Marktkapital")

    # --- Kauf-/Verkaufsverhaeltnis ---
    if kaeufe is not None and verkaeufe is not None and (kaeufe + verkaeufe):
        messbar += 1
        gesamt = kaeufe + verkaeufe
        anteil = kaeufe / gesamt
        if gesamt < 20:
            funde.append((15, "nur %d Trades in 24 Stunden" % gesamt))
        if anteil > 0.9 and gesamt > 50:
            funde.append((20, "%.0f%% Kaeufe bei %d Trades - unnatuerlich "
                              "einseitig" % (anteil * 100, gesamt)))
    else:
        ungeprueft.append("Kauf-/Verkaufsverhaeltnis")

    # --- Kurssprung ---
    if aend_24h is None:
        ungeprueft.append("24h-Kursveraenderung")
    else:
        messbar += 1
        if aend_24h > 300:
            funde.append((25, "Kurs in 24 Stunden um %.0f %% gestiegen - "
                              "wer jetzt kauft, kauft die Spitze"
                          % aend_24h))
        elif aend_24h < -60:
            funde.append((25, "Kurs in 24 Stunden um %.0f %% gefallen"
                          % aend_24h))

    punkte = min(100, sum(g for g, _ in funde))

    # --- Einstufung ---
    if messbar < 3:
        stufe = "UNKNOWN"
    elif punkte >= 60:
        stufe = "EXTREME"
    elif punkte >= 35:
        stufe = "HIGH"
    elif punkte >= 15:
        stufe = "MEDIUM"
    else:
        stufe = "LOW"

    return Risikobefund(stufe, punkte, funde, ungeprueft)
