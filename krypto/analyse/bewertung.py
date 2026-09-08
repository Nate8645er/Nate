# KRYPTO - Bewertung.
#
# Aus Kerzen wird eine Zahl, aus der Zahl eine Entscheidung. Die
# Reihenfolge ist fest und nachvollziehbar:
#
#   Datenpruefung -> Trend -> Momentum -> Volatilitaet -> Liquiditaet
#   -> Risiko-Score -> Chancen-Score -> TRADE / NO TRADE
#
# Zwei Regeln, die nicht verhandelbar sind:
#   1. Bei Unsicherheit: NO TRADE. Jeder fehlende Indikator ist ein
#      Grund gegen den Trade, nie einer dafuer.
#   2. Nur Long. Ohne Broker-Anbindung gibt es keine Leerverkaeufe -
#      also wird auch keiner signalisiert.
#
# Was dieses Modul NICHT ist: eine Vorhersage. Ein hoher Chancen-Score
# heisst, dass mehrere Bedingungen gleichzeitig zutreffen, die
# historisch oft vor Aufwaertsbewegungen zu sehen waren. Er heisst
# nicht, dass der Kurs steigt.

from krypto import konfig
from krypto.analyse import indikatoren as ind
from krypto.daten import pruefung


class Bewertung:
    def __init__(self):
        self.entscheid = "NO TRADE"
        self.chance = 0.0
        self.risiko = 100.0
        # Drei Listen, und der Unterschied ist wichtig:
        #   gruende  - was fuer einen Einstieg spricht
        #   hinweise - was Risikopunkte kostet, aber nicht verbietet
        #   blocker  - harte Vetos. Ein einziges genuegt fuer NO TRADE.
        # Solange beides in einem Topf lag, war der Risiko-Score
        # wirkungslos: jede Notiz wirkte wie ein Verbot.
        self.gruende = []
        self.hinweise = []
        self.blocker = []
        self.werte = {}            # rohe Indikatorstaende
        self.datenbefund = None

    def __repr__(self):
        return "<Bewertung %s Chance=%.0f Risiko=%.0f>" % (
            self.entscheid, self.chance, self.risiko)

    def kurzbegruendung(self):
        """Das Wichtigste zuerst: Vetos, sonst Hinweise, sonst Pro-Gruende."""
        return "; ".join(self.blocker or self.hinweise or self.gruende)

    def zeile(self, name=""):
        return "%-10s %-9s Chance %3.0f  Risiko %3.0f  %s" % (
            name, self.entscheid, self.chance, self.risiko,
            self.kurzbegruendung()[:70])


def bewerten(kerzen, kandidat=None, jetzt=None, daten_pruefen=True):
    """Bewertet die Lage am ENDE der uebergebenen Kerzenreihe.

    Fuer den Backtest wird eine gekuerzte Reihe uebergeben. Dadurch kann
    diese Funktion strukturell nicht in die Zukunft sehen: was sie nicht
    bekommt, kann sie nicht verwenden.
    """
    b = Bewertung()

    # --- 1. Datenqualitaet -------------------------------------------
    if daten_pruefen:
        befund = pruefung.kerzen_pruefen(
            kerzen, konfig.MIN_KERZEN, konfig.DATEN_MAX_ALTER_S, jetzt)
    else:
        befund = pruefung.Befund(len(kerzen) >= konfig.MIN_KERZEN,
                                 [] if len(kerzen) >= konfig.MIN_KERZEN
                                 else ["zu wenige Kerzen"])
    b.datenbefund = befund
    if not befund:
        b.blocker.append("Datenpruefung: " + "; ".join(befund.gruende))
        return b

    o, h, t, s = ind.zerlegen(kerzen)
    kurs = s[-1]

    ema_kurz = ind.ema(s, 12)[-1]
    ema_lang = ind.ema(s, 26)[-1]
    ema_sehr_lang = ind.ema(s, 50)[-1] if len(s) >= 50 else None
    rsi_wert = ind.rsi(s, 14)[-1]
    m_linie, m_signal, m_hist = ind.macd(s)
    atr_wert = ind.atr(h, t, s, 14)[-1]
    vola = ind.volatilitaet(s, 20)
    lage = ind.regime(vola)
    marken = ind.marken(h, t, fenster=5)

    b.werte = {
        "kurs": kurs, "ema12": ema_kurz, "ema26": ema_lang,
        "ema50": ema_sehr_lang, "rsi14": rsi_wert,
        "macd": m_linie[-1], "macd_signal": m_signal[-1],
        "macd_hist": m_hist[-1], "atr14": atr_wert,
        "vola20": vola[-1], "regime": lage,
        "atr_anteil": (atr_wert / kurs) if (atr_wert and kurs) else None,
        "widerstand": marken["widerstand"][:1],
        "unterstuetzung": marken["unterstuetzung"][:1],
    }

    fehlend = [n for n, v in (("EMA12", ema_kurz), ("EMA26", ema_lang),
                              ("RSI", rsi_wert), ("MACD", m_hist[-1]),
                              ("ATR", atr_wert)) if v is None]
    if fehlend:
        b.blocker.append("Indikatoren ohne Wert: " + ", ".join(fehlend))
        return b

    # --- 2. Chance ----------------------------------------------------
    # Fuenf Bedingungen, je 20 Punkte. Bewusst simpel: ein Modell, das
    # niemand nachrechnen kann, wird niemandem helfen, wenn es schiefgeht.
    chance = 0.0
    if ema_kurz > ema_lang:
        chance += 20
        b.gruende.append("EMA12 ueber EMA26 (Aufwaertstrend)")
    if ema_sehr_lang is not None and kurs > ema_sehr_lang:
        chance += 20
        b.gruende.append("Kurs ueber EMA50")
    elif ema_sehr_lang is None:
        b.gruende.append("EMA50 fehlt - 20 Punkte nicht vergeben")
    if m_hist[-1] > 0:
        chance += 20
        b.gruende.append("MACD-Histogramm positiv")
    if 45 <= rsi_wert <= 68:
        chance += 20
        b.gruende.append("RSI %.0f im gesunden Band" % rsi_wert)
    elif rsi_wert < 30:
        chance += 8
        b.gruende.append("RSI %.0f ueberverkauft - Teilpunkte" % rsi_wert)
    if len(s) >= 21 and s[-1] > s[-21]:
        chance += 20
        b.gruende.append("Kurs ueber Stand vor 20 Kerzen")
    b.chance = round(min(chance, 100.0), 1)

    # --- 3. Risiko ----------------------------------------------------
    risiko = 0.0
    anteil = atr_wert / kurs if kurs else None
    if anteil is not None:
        # ATR von 2 % des Kurses -> 40 Punkte. Linear, gedeckelt.
        risiko += min(anteil * 2000, 45)
    else:
        risiko += 45
    if lage == "wild":
        risiko += 20
        b.blocker.append("Volatilitaetsregime wild")     # hartes Veto
    elif lage == "unbekannt":
        risiko += 15
        b.hinweise.append("Volatilitaetsregime unbekannt")
    if rsi_wert > 78:
        risiko += 20
        b.blocker.append("RSI %.0f - ueberkauft" % rsi_wert)   # hartes Veto
    if ema_sehr_lang is not None and kurs < ema_sehr_lang:
        risiko += 15
        b.hinweise.append("Kurs unter EMA50")
    if befund.hinweise:
        risiko += 10
        b.hinweise.append("Datenhinweis: " + "; ".join(befund.hinweise))

    # Liquiditaet aus dem Marktdatensatz, wenn vorhanden.
    if kandidat is not None:
        if not getattr(kandidat, "befund", None) or not kandidat.befund:
            risiko += 30
            # Unter der Volumen- oder Marktkapitalgrenze wird nicht
            # gehandelt. Das ist ein Veto, kein Abzug.
            b.blocker.append("Liquiditaetspruefung nicht bestanden")
        else:
            u = kandidat.umschlag
            if u is not None and u < 0.02:
                # Ein niedriger Umschlag ist bei den groessten Werten
                # normal - BTC liegt regelmaessig darunter. Das kostet
                # Punkte, es verbietet nichts.
                risiko += 10
                b.hinweise.append("Umschlag unter 2 % des Marktkapitals")
    else:
        risiko += 5   # ohne Liquiditaetsdaten bleibt ein Restzweifel
        b.hinweise.append("keine Liquiditaetsdaten uebergeben")
    b.risiko = round(min(risiko, 100.0), 1)

    # --- 4. Entscheid -------------------------------------------------
    if b.chance < konfig.CHANCE_SCHWELLE:
        b.blocker.append("Chance %.0f unter Schwelle %.0f"
                         % (b.chance, konfig.CHANCE_SCHWELLE))
    if b.risiko > konfig.RISIKO_SCHWELLE:
        b.blocker.append("Risiko %.0f ueber Schwelle %.0f"
                         % (b.risiko, konfig.RISIKO_SCHWELLE))
    b.entscheid = "NO TRADE" if b.blocker else "TRADE"
    return b


def stop_und_ziel(kurs, atr_wert,
                  stop_faktor=None, ziel_faktor=None):
    """Stop-Loss und Take-Profit aus der Volatilitaet, nicht aus dem Bauch.

    Ohne ATR gibt es keinen Stop - und ohne Stop gibt es keine Order.
    Deshalb (None, None) statt eines geratenen Prozentwerts.
    """
    if not atr_wert or not kurs or atr_wert <= 0:
        return None, None
    sf = konfig.STOP_ATR_FAKTOR if stop_faktor is None else stop_faktor
    zf = konfig.ZIEL_ATR_FAKTOR if ziel_faktor is None else ziel_faktor
    stop = kurs - sf * atr_wert
    if stop <= 0:
        return None, None
    return stop, kurs + zf * atr_wert
