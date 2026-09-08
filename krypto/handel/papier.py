# KRYPTO - Papierhandel.
#
# Ein vollstaendiges Depot ohne einen einzigen echten Franken: Geld,
# Positionen, Orders, Gebuehren, Slippage, Stop-Loss, Take-Profit,
# Historie. Es rechnet absichtlich pessimistisch - Kauf zum leicht
# hoeheren, Verkauf zum leicht tieferen Kurs, Gebuehr auf beiden Seiten.
#
# Wer im Papierhandel keinen Gewinn macht, macht mit echtem Geld erst
# recht keinen. Das ist der ganze Zweck dieser Datei.

import datetime
import json
import os

from krypto import konfig
from krypto.betrieb import protokoll


def _jetzt(zeit=None):
    if zeit is None:
        return datetime.datetime.now(datetime.timezone.utc)
    if isinstance(zeit, (int, float)):
        return datetime.datetime.fromtimestamp(zeit, datetime.timezone.utc)
    return zeit


class Position:
    def __init__(self, symbol, menge, einstieg, stop, ziel, eroeffnet,
                 gebuehr_bezahlt=0.0):
        self.symbol = symbol
        self.menge = menge
        self.einstieg = einstieg
        self.stop = stop
        self.ziel = ziel
        self.eroeffnet = eroeffnet
        self.letzter_kurs = einstieg
        self.gebuehr_bezahlt = gebuehr_bezahlt

    def wert(self, kurs=None):
        return self.menge * (kurs if kurs is not None else self.letzter_kurs)

    def ergebnis(self, kurs=None):
        k = kurs if kurs is not None else self.letzter_kurs
        return (k - self.einstieg) * self.menge

    def als_dict(self):
        return {"symbol": self.symbol, "menge": self.menge,
                "einstieg": self.einstieg, "stop": self.stop,
                "ziel": self.ziel, "eroeffnet": self.eroeffnet,
                "letzter_kurs": self.letzter_kurs,
                "gebuehr_bezahlt": self.gebuehr_bezahlt}

    @classmethod
    def aus_dict(cls, d):
        p = cls(d["symbol"], d["menge"], d["einstieg"], d.get("stop"),
                d.get("ziel"), d.get("eroeffnet"), d.get("gebuehr_bezahlt", 0))
        p.letzter_kurs = d.get("letzter_kurs", d["einstieg"])
        return p


class Depot:
    DATEI = os.path.join(konfig.ZUSTAND, "papierdepot.json")

    def __init__(self, kapital=None, gebuehr=None, slippage=None):
        self.kapital_start = konfig.KAPITAL_START if kapital is None else kapital
        self.geld = self.kapital_start
        self.gebuehr = konfig.GEBUEHR if gebuehr is None else gebuehr
        self.slippage = konfig.SLIPPAGE if slippage is None else slippage
        self.positionen = {}
        self.historie = []
        self.hoechststand = self.kapital_start
        self.kapital_tagesbeginn = self.kapital_start
        self.tag = None

    # --- Zustand ------------------------------------------------------

    @property
    def freies_geld(self):
        return self.geld

    def gesamtwert(self):
        return self.geld + sum(p.wert() for p in self.positionen.values())

    def tageswechsel(self, zeit=None):
        heute = _jetzt(zeit).date().isoformat()
        if self.tag != heute:
            self.tag = heute
            self.kapital_tagesbeginn = self.gesamtwert()
        return heute

    def tagesergebnis(self, zeit=None):
        self.tageswechsel(zeit)
        return self.gesamtwert() - self.kapital_tagesbeginn

    def trades_heute(self, zeit=None):
        heute = _jetzt(zeit).date().isoformat()
        return sum(1 for e in self.historie
                   if e.get("art") == "kauf" and str(e.get("zeit", ""))[:10] == heute)

    def _hoch_nachfuehren(self):
        self.hoechststand = max(self.hoechststand, self.gesamtwert())

    def drawdown(self):
        if self.hoechststand <= 0:
            return 0.0
        return (self.hoechststand - self.gesamtwert()) / self.hoechststand

    # --- Handel -------------------------------------------------------

    def kaufen(self, symbol, menge, kurs, stop, ziel, zeit=None, grund=""):
        """Kauft zum Marktkurs plus Slippage, Gebuehr obendrauf.

        Diese Methode prueft KEINE Risikogrenzen - das macht
        risiko.wache.order_pruefen. Getrennte Zustaendigkeiten: hier die
        Buchhaltung, dort das Verbot.
        """
        self.tageswechsel(zeit)
        if menge <= 0 or kurs <= 0:
            raise ValueError("Menge und Kurs muessen positiv sein")
        if symbol in self.positionen:
            raise ValueError("Position in %s besteht bereits" % symbol)

        ausgefuehrt = kurs * (1 + self.slippage)
        volumen = menge * ausgefuehrt
        gebuehr = volumen * self.gebuehr
        if volumen + gebuehr > self.geld + 1e-9:
            raise ValueError("nicht genug Geld: braucht %.2f, hat %.2f"
                             % (volumen + gebuehr, self.geld))

        self.geld -= volumen + gebuehr
        self.positionen[symbol] = Position(
            symbol, menge, ausgefuehrt, stop, ziel,
            _jetzt(zeit).isoformat(timespec="seconds"), gebuehr)
        eintrag = {
            "art": "kauf", "symbol": symbol, "menge": menge,
            "kurs": ausgefuehrt, "gebuehr": gebuehr, "stop": stop,
            "ziel": ziel, "grund": grund,
            "zeit": _jetzt(zeit).isoformat(timespec="seconds"),
            "geld_danach": self.geld,
        }
        self.historie.append(eintrag)
        self._hoch_nachfuehren()
        protokoll.trade("kauf", **eintrag)
        return eintrag

    def verkaufen(self, symbol, kurs, zeit=None, grund="manuell"):
        self.tageswechsel(zeit)
        p = self.positionen.get(symbol)
        if p is None:
            raise ValueError("keine Position in %s" % symbol)

        ausgefuehrt = kurs * (1 - self.slippage)
        volumen = p.menge * ausgefuehrt
        gebuehr = volumen * self.gebuehr
        self.geld += volumen - gebuehr

        einsatz = p.menge * p.einstieg
        netto = volumen - gebuehr - einsatz - p.gebuehr_bezahlt
        eintrag = {
            "art": "verkauf", "symbol": symbol, "menge": p.menge,
            "kurs": ausgefuehrt, "einstieg": p.einstieg, "gebuehr": gebuehr,
            "ergebnis": netto,
            "ergebnis_anteil": netto / einsatz if einsatz else 0.0,
            "grund": grund, "eroeffnet": p.eroeffnet,
            "zeit": _jetzt(zeit).isoformat(timespec="seconds"),
            "geld_danach": self.geld,
        }
        del self.positionen[symbol]
        self.historie.append(eintrag)
        self._hoch_nachfuehren()
        protokoll.trade("verkauf", **eintrag)
        return eintrag

    def kurse_setzen(self, kurse, zeit=None, kerze=None):
        """Neue Kurse einspielen und Stop/Ziel pruefen.

        'kerze' ist optional {symbol: (hoch, tief)}. Damit wird der Stop
        auch dann ausgeloest, wenn er innerhalb einer Kerze gerissen und
        bis zum Schluss wieder ueberschritten wurde. Ohne diese Angabe
        wuerde ein Backtest die Verluste systematisch zu klein rechnen.

        Reisst eine Kerze Stop UND Ziel, wird der Stop angenommen. Was
        zuerst kam, ist aus OHLC nicht erkennbar - und die vorsichtige
        Annahme ist die einzige ehrliche.
        """
        ausloesungen = []
        for symbol, kurs in kurse.items():
            p = self.positionen.get(symbol)
            if p is None:
                continue
            p.letzter_kurs = kurs
            hoch = tief = kurs
            if kerze and symbol in kerze:
                hoch, tief = kerze[symbol]

            if p.stop is not None and tief <= p.stop:
                ausloesungen.append(
                    self.verkaufen(symbol, p.stop, zeit, "stop-loss"))
            elif p.ziel is not None and hoch >= p.ziel:
                ausloesungen.append(
                    self.verkaufen(symbol, p.ziel, zeit, "take-profit"))
        self._hoch_nachfuehren()
        return ausloesungen

    # --- Auswertung ---------------------------------------------------

    def kennzahlen(self):
        verkaeufe = [e for e in self.historie if e["art"] == "verkauf"]
        gewinne = [e for e in verkaeufe if e["ergebnis"] > 0]
        verluste = [e for e in verkaeufe if e["ergebnis"] <= 0]
        summe_g = sum(e["ergebnis"] for e in gewinne)
        summe_v = abs(sum(e["ergebnis"] for e in verluste))
        gebuehren = sum(e.get("gebuehr", 0) for e in self.historie)
        return {
            "kapital_start": self.kapital_start,
            "gesamtwert": self.gesamtwert(),
            "geld": self.geld,
            "rendite": (self.gesamtwert() / self.kapital_start - 1)
                       if self.kapital_start else 0.0,
            "offene_positionen": len(self.positionen),
            "abgeschlossen": len(verkaeufe),
            "treffer": len(gewinne),
            "trefferquote": len(gewinne) / len(verkaeufe) if verkaeufe else None,
            "profitfaktor": (summe_g / summe_v) if summe_v > 0
                            else (None if not gewinne else float("inf")),
            "gebuehren_gesamt": gebuehren,
            "hoechststand": self.hoechststand,
            "drawdown_jetzt": self.drawdown(),
        }

    # --- Persistenz ---------------------------------------------------

    def speichern(self, pfad=None):
        pfad = pfad or self.DATEI
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        daten = {
            "kapital_start": self.kapital_start, "geld": self.geld,
            "gebuehr": self.gebuehr, "slippage": self.slippage,
            "hoechststand": self.hoechststand,
            "kapital_tagesbeginn": self.kapital_tagesbeginn, "tag": self.tag,
            "positionen": {s: p.als_dict()
                           for s, p in self.positionen.items()},
            "historie": self.historie,
        }
        # Erst daneben schreiben, dann umbenennen. Ein Absturz mitten im
        # Schreiben darf das Depot nicht zerstoeren.
        vorlaeufig = pfad + ".neu"
        with open(vorlaeufig, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=1, default=str)
        os.replace(vorlaeufig, pfad)
        return pfad

    @classmethod
    def laden(cls, pfad=None):
        pfad = pfad or cls.DATEI
        try:
            with open(pfad, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            return cls()
        depot = cls(d.get("kapital_start"), d.get("gebuehr"), d.get("slippage"))
        depot.geld = d.get("geld", depot.kapital_start)
        depot.hoechststand = d.get("hoechststand", depot.kapital_start)
        depot.kapital_tagesbeginn = d.get("kapital_tagesbeginn",
                                          depot.kapital_start)
        depot.tag = d.get("tag")
        depot.positionen = {s: Position.aus_dict(p)
                            for s, p in (d.get("positionen") or {}).items()}
        depot.historie = d.get("historie") or []
        return depot
