# KRYPTO - Signal-Engine.
#
# Acht Kennzahlen von 0 bis 100. Jede sagt mit, WORAUS sie gerechnet
# ist und WAS gefehlt hat.
#
# Die wichtigste Klasse dieser Datei ist nicht die Rechnung, sondern
# DATA_INCOMPLETE. Fehlt eine Eingabe, gibt es keine Zahl - keinen
# Mittelwert, keinen Standardwert, keine 50 als "neutral". Eine 50 aus
# fehlenden Daten sieht in einer Tabelle genauso aus wie eine 50 aus
# einer Messung, und das ist der Unterschied zwischen einem Werkzeug
# und einer Attrappe.
#
# Was hier fehlt und warum:
#   SOCIAL_SENTIMENT ist fast immer DATA_INCOMPLETE. Reddit antwortet
#   aus Rechenzentren mit HTTP 403, X/Twitter kostet, Telegram und
#   Discord brauchen ein Bot-Konto in der Gruppe. Es gibt also keine
#   Messung - und deshalb keine Zahl.

FEHLT = "DATA_INCOMPLETE"


class Wert:
    """Eine Kennzahl. Entweder eine Zahl mit Begruendung, oder FEHLT."""

    def __init__(self, name, punkte=None, teile=None, fehlend=None):
        self.name = name
        self.punkte = punkte
        self.teile = teile or []          # (Beschreibung, Beitrag)
        self.fehlend = fehlend or []      # was nicht gemessen werden konnte

    @property
    def vollstaendig(self):
        return self.punkte is not None

    def __repr__(self):
        return "<%s %s>" % (self.name, self.anzeige())

    def anzeige(self):
        if not self.vollstaendig:
            return FEHLT
        return "%.0f/100" % self.punkte

    def zeile(self):
        if not self.vollstaendig:
            return "%-18s %-16s  fehlt: %s" % (
                self.name, FEHLT, "; ".join(self.fehlend)[:60])
        return "%-18s %-16s  %s" % (
            self.name, self.anzeige(),
            "; ".join("%s %+d" % (t, p) for t, p in self.teile)[:60])


def _deckel(x):
    return max(0.0, min(100.0, x))


# --- Einzelne Kennzahlen ---------------------------------------------

def marktmomentum(aend_1h=None, aend_24h=None, aend_7d=None):
    """Bewegt sich der Kurs, und in welche Richtung?"""
    teile, fehlend, punkte = [], [], 50.0
    if aend_24h is None:
        fehlend.append("24h-Veraenderung")
    else:
        beitrag = max(-30, min(30, aend_24h * 1.5))
        punkte += beitrag
        teile.append(("24h %+.1f%%" % aend_24h, beitrag))
    if aend_7d is None:
        fehlend.append("7d-Veraenderung")
    else:
        beitrag = max(-20, min(20, aend_7d * 0.7))
        punkte += beitrag
        teile.append(("7d %+.1f%%" % aend_7d, beitrag))
    if aend_1h is not None:
        beitrag = max(-10, min(10, aend_1h * 2))
        punkte += beitrag
        teile.append(("1h %+.1f%%" % aend_1h, beitrag))
    if aend_24h is None and aend_7d is None:
        return Wert("MARKET_MOMENTUM", None, fehlend=fehlend)
    return Wert("MARKET_MOMENTUM", _deckel(punkte), teile, fehlend)


def liquiditaet(liq_usd=None, volumen_24h=None, marktkapital=None):
    """Kommt man wieder raus? Das ist die Frage, die zaehlt."""
    teile, fehlend, punkte = [], [], 0.0
    if liq_usd is None:
        return Wert("LIQUIDITY", None, fehlend=["Liquiditaet in USD"])
    # Schwellen aus der Praxis: unter 50k ist eine Position kaum
    # aufloesbar, ueber 5 Mio ist sie fuer Privatgroessen unkritisch.
    for grenze, p in ((50_000, 10), (250_000, 25), (1_000_000, 45),
                      (5_000_000, 70), (25_000_000, 90)):
        if liq_usd >= grenze:
            punkte = p
    if liq_usd >= 100_000_000:
        punkte = 100
    teile.append(("Liquiditaet %.0f USD" % liq_usd, punkte))

    if volumen_24h is None:
        fehlend.append("24h-Volumen")
    elif liq_usd > 0:
        u = volumen_24h / liq_usd
        if u < 0.05:
            punkte -= 15
            teile.append(("Umschlag %.2f - kaum Handel" % u, -15))
        elif u > 20:
            # Sehr viel Volumen auf wenig Tiefe. Das ist kein gutes
            # Zeichen, sondern das Muster von Wash-Trading.
            punkte -= 20
            teile.append(("Umschlag %.1f - auffaellig hoch" % u, -20))
        else:
            punkte += 5
            teile.append(("Umschlag %.2f gesund" % u, 5))
    if marktkapital is None:
        fehlend.append("Marktkapitalisierung")
    return Wert("LIQUIDITY", _deckel(punkte), teile, fehlend)


def onchain_staerke(kette_erreichbar=None, kaeufe=None, verkaeufe=None,
                    alter_tage=None):
    """Was auf der Kette wirklich passiert - soweit ohne Schluessel sichtbar.

    Ohne Etherscan/Nansen/Arkham sehen wir keine Halterverteilung und
    kein Smart Money. Was DexScreener liefert, sind Kauf- und
    Verkaufszahlen. Mehr behauptet dieses Mass nicht.
    """
    teile, fehlend, punkte = [], [], 50.0
    if kette_erreichbar is False:
        return Wert("ONCHAIN_STRENGTH", None,
                    fehlend=["Kette nicht erreichbar"])
    if kaeufe is None or verkaeufe is None:
        fehlend.append("Kauf-/Verkaufszahlen")
    else:
        gesamt = kaeufe + verkaeufe
        if gesamt < 30:
            fehlend.append("zu wenige Transaktionen (%d) fuer eine Aussage"
                           % gesamt)
        else:
            anteil = kaeufe / gesamt
            beitrag = max(-35, min(35, (anteil - 0.5) * 140))
            punkte += beitrag
            teile.append(("%.0f%% Kaeufe von %d Trades"
                          % (anteil * 100, gesamt), beitrag))
    if alter_tage is None:
        fehlend.append("Alter des Paares")
    elif alter_tage < 3:
        punkte -= 25
        teile.append(("Paar erst %.1f Tage alt" % alter_tage, -25))
    elif alter_tage > 180:
        punkte += 10
        teile.append(("Paar %.0f Tage alt" % alter_tage, 10))
    if not teile:
        return Wert("ONCHAIN_STRENGTH", None, fehlend=fehlend)
    return Wert("ONCHAIN_STRENGTH", _deckel(punkte), teile, fehlend)


def nachrichten_momentum(erwaehnungen=None, gesamt_schlagzeilen=None):
    """Wie oft steht der Wert gerade in den Schlagzeilen?

    Menge, nicht Ton. Ob eine Erwaehnung gut oder schlecht ist, sagt
    dieses Mass nicht - und tut auch nicht so.
    """
    if erwaehnungen is None or gesamt_schlagzeilen is None:
        return Wert("NEWS_MOMENTUM", None,
                    fehlend=["keine Schlagzeilen abgerufen"])
    if gesamt_schlagzeilen == 0:
        return Wert("NEWS_MOMENTUM", None,
                    fehlend=["Feeds lieferten null Schlagzeilen"])
    if erwaehnungen == 0:
        return Wert("NEWS_MOMENTUM", 0.0,
                    [("0 von %d Schlagzeilen" % gesamt_schlagzeilen, 0)])
    punkte = _deckel(min(100.0, erwaehnungen * 25.0))
    return Wert("NEWS_MOMENTUM", punkte,
                [("%d von %d Schlagzeilen" % (erwaehnungen,
                                              gesamt_schlagzeilen), punkte)])


def soziale_stimmung(quellen=None):
    """Social Sentiment.

    Ohne bezahlte oder kontogebundene Quelle gibt es hier nichts zu
    messen. Diese Funktion liefert deshalb im Normalfall FEHLT - und
    das ist die richtige Antwort, nicht ein Mangel.
    """
    if not quellen:
        return Wert("SOCIAL_SENTIMENT", None, fehlend=[
            "Reddit HTTP 403 aus Rechenzentren",
            "X/Twitter kostenpflichtig",
            "Telegram/Discord brauchen Bot-Konto"])
    gesamt = sum(q.get("punkte", 0) for q in quellen) / len(quellen)
    return Wert("SOCIAL_SENTIMENT", _deckel(gesamt),
                [(q.get("name", "?"), q.get("punkte", 0)) for q in quellen])


def fomo_signal(marktmoment, nachrichten, im_trend=None, angst_gier=None):
    """Wie stark ist die Aufmerksamkeit gerade - und ist sie schon spaet?

    Ein hoher FOMO-Wert ist ausdruecklich KEIN Kaufsignal. Er misst,
    wie viel Aufmerksamkeit auf einem Wert liegt. Genau dann ist die
    Bewegung oft schon gelaufen, und genau dann kaufen die meisten.
    """
    teile, fehlend, punkte = [], [], 0.0
    gemessen = False
    if marktmoment.vollstaendig:
        beitrag = marktmoment.punkte * 0.4
        punkte += beitrag
        teile.append(("Momentum %.0f" % marktmoment.punkte, beitrag))
        gemessen = True
    else:
        fehlend.append("Marktmomentum")
    if nachrichten.vollstaendig:
        beitrag = nachrichten.punkte * 0.3
        punkte += beitrag
        teile.append(("Nachrichten %.0f" % nachrichten.punkte, beitrag))
        gemessen = True
    else:
        fehlend.append("Nachrichtenmomentum")
    if im_trend is None:
        fehlend.append("Trendliste")
    elif im_trend:
        punkte += 20
        teile.append(("in der CoinGecko-Trendliste", 20))
        gemessen = True
    if angst_gier is None:
        fehlend.append("Fear-and-Greed")
    else:
        beitrag = (angst_gier - 50) * 0.2
        punkte += beitrag
        teile.append(("Markt-Gier %d" % angst_gier, beitrag))
        gemessen = True
    if not gemessen:
        return Wert("FOMO_SIGNAL", None, fehlend=fehlend)
    return Wert("FOMO_SIGNAL", _deckel(punkte), teile, fehlend)


def zusammenstellen(werte):
    """Alle Kennzahlen mit einer ehrlichen Vollstaendigkeitsangabe."""
    voll = [w for w in werte if w.vollstaendig]
    return {
        "werte": {w.name: (w.punkte if w.vollstaendig else FEHLT)
                  for w in werte},
        "gemessen": len(voll),
        "gesamt": len(werte),
        "vollstaendigkeit": len(voll) / len(werte) if werte else 0.0,
        "fehlend": {w.name: w.fehlend for w in werte if not w.vollstaendig},
    }
