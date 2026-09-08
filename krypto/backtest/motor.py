# KRYPTO - Backtest.
#
# Der Punkt, an dem sich jedes Handelssystem selbst belaegt, ist die
# Zeit. Deshalb steht die Regel hier ganz oben und wird im Code
# eingehalten, nicht nur behauptet:
#
#   Entschieden wird auf dem SCHLUSS von Kerze i - und zwar
#   ausschliesslich mit Kerzen[0..i]. Ausgefuehrt wird zur EROEFFNUNG
#   von Kerze i+1. Stop und Ziel werden ab Kerze i+1 an Hoch und Tief
#   geprueft, nicht am Schlusskurs.
#
# Damit ist ein Blick in die Zukunft strukturell ausgeschlossen: die
# Bewertungsfunktion bekommt physisch nur die Vergangenheit uebergeben.
# Reisst eine Kerze Stop und Ziel gleichzeitig, gilt der Stop.
#
# Gebuehren und Slippage sind immer an. Ein Backtest ohne Kosten ist
# eine Werbebroschuere.

import math

from krypto import konfig
from krypto.analyse import bewertung as bw
from krypto.analyse import indikatoren as ind
from krypto.handel import papier
from krypto.risiko import groesse


class Ergebnis:
    def __init__(self, depot, kurve, symbol, kerzen_gesamt, entscheide):
        self.depot = depot
        self.kurve = kurve                # Depotwert je Kerze
        self.symbol = symbol
        self.kerzen_gesamt = kerzen_gesamt
        self.entscheide = entscheide      # (index, entscheid, chance, risiko)

    def max_drawdown(self):
        hoch, tief = 0.0, 0.0
        for w in self.kurve:
            hoch = max(hoch, w)
            if hoch > 0:
                tief = max(tief, (hoch - w) / hoch)
        return tief

    def sharpe(self):
        """Sharpe je Kerze, ohne risikofreien Zins, dann annualisiert
        auf die Anzahl Kerzen der Reihe. Bei weniger als 3 Renditen
        oder ohne Streuung: None statt einer Zahl, die nichts aussagt."""
        renditen = []
        for i in range(1, len(self.kurve)):
            v = self.kurve[i - 1]
            if v > 0:
                renditen.append((self.kurve[i] - v) / v)
        if len(renditen) < 3:
            return None
        mittel = sum(renditen) / len(renditen)
        var = sum((r - mittel) ** 2 for r in renditen) / (len(renditen) - 1)
        if var <= 0:
            return None
        return (mittel / math.sqrt(var)) * math.sqrt(len(renditen))

    def bericht(self):
        k = self.depot.kennzahlen()
        return {
            "symbol": self.symbol,
            "kerzen": self.kerzen_gesamt,
            "kapital_start": k["kapital_start"],
            "kapital_ende": k["gesamtwert"],
            "rendite": k["rendite"],
            "trades": k["abgeschlossen"],
            "trefferquote": k["trefferquote"],
            "profitfaktor": k["profitfaktor"],
            "max_drawdown": self.max_drawdown(),
            "sharpe": self.sharpe(),
            "gebuehren_gesamt": k["gebuehren_gesamt"],
            "offene_positionen": k["offene_positionen"],
            "signale_trade": sum(1 for e in self.entscheide if e[1] == "TRADE"),
            "signale_gesamt": len(self.entscheide),
        }


def laufen(kerzen, symbol="TEST", kapital=None, vorlauf=None,
           bewerter=None):
    """Backtest ueber eine Kerzenreihe. Long-only, eine Position."""
    vorlauf = konfig.MIN_KERZEN if vorlauf is None else vorlauf
    bewerter = bewerter or (
        lambda teil: bw.bewerten(teil, daten_pruefen=False))

    depot = papier.Depot(kapital=kapital)
    kurve, entscheide = [], []

    if len(kerzen) <= vorlauf + 1:
        return Ergebnis(depot, [depot.gesamtwert()], symbol, len(kerzen), [])

    for i in range(vorlauf, len(kerzen) - 1):
        naechste = kerzen[i + 1]
        zeit_naechste = naechste[0] / 1000.0
        o, h, t, s = naechste[1], naechste[2], naechste[3], naechste[4]

        # 1. Offene Position an Hoch/Tief der naechsten Kerze pruefen.
        depot.kurse_setzen({symbol: s}, zeit=zeit_naechste,
                           kerze={symbol: (h, t)})

        # 2. Entscheiden - nur mit dem, was bis Kerze i bekannt war.
        if symbol not in depot.positionen:
            teil = kerzen[:i + 1]
            b = bewerter(teil)
            entscheide.append((i, b.entscheid, b.chance, b.risiko))
            if b.entscheid == "TRADE":
                atr_wert = b.werte.get("atr14")
                einstieg = o                     # Eroeffnung Kerze i+1
                stop, ziel = bw.stop_und_ziel(einstieg, atr_wert)
                if stop is not None:
                    g = groesse.berechnen(depot.gesamtwert(), depot.geld,
                                          einstieg, stop)
                    if g.menge > 0:
                        try:
                            depot.kaufen(symbol, g.menge, einstieg, stop, ziel,
                                         zeit=zeit_naechste,
                                         grund="Chance %.0f" % b.chance)
                        except ValueError:
                            pass
                        # Stop kann schon in der Einstiegskerze reissen.
                        depot.kurse_setzen({symbol: s}, zeit=zeit_naechste,
                                           kerze={symbol: (h, t)})
        kurve.append(depot.gesamtwert())

    # Am Ende offene Position zum letzten Schlusskurs schliessen, damit
    # das Ergebnis kein unrealisiertes Versprechen enthaelt.
    if symbol in depot.positionen:
        depot.verkaufen(symbol, kerzen[-1][4],
                        zeit=kerzen[-1][0] / 1000.0, grund="testende")
        kurve.append(depot.gesamtwert())

    return Ergebnis(depot, kurve or [depot.gesamtwert()], symbol,
                    len(kerzen), entscheide)


def kaufen_und_halten(kerzen, vorlauf=None):
    """Vergleichsmassstab. Ein System, das schlechter ist als einfach
    kaufen und liegenlassen, hat keinen Daseinsgrund."""
    vorlauf = konfig.MIN_KERZEN if vorlauf is None else vorlauf
    if len(kerzen) <= vorlauf + 1:
        return None
    ein = kerzen[vorlauf + 1][1]
    aus = kerzen[-1][4]
    brutto = aus / ein - 1
    kosten = 2 * (konfig.GEBUEHR + konfig.SLIPPAGE)
    return brutto - kosten
