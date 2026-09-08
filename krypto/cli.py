# KRYPTO - Bedienung.
#
#   python3 -m krypto.cli <befehl> [optionen]
#
# Jeder Befehl schreibt, woher seine Zahlen kommen, und sagt es, wenn
# er nichts weiss. Kein Befehl dieses Programms kann eine echte Order
# ausloesen.

import argparse
import datetime
import json
import sys

from krypto import konfig
from krypto.analyse import bewertung as bw
from krypto.backtest import motor
from krypto.betrieb import protokoll
from krypto.daten import quelle, universum
from krypto.handel import papier, tor
from krypto.risiko import groesse, wache


def _linie(zeichen="-", n=68):
    print(zeichen * n)


def _kopf(titel):
    _linie("=")
    print(titel)
    _linie("=")


def _herkunft(h):
    return "%s, Alter %ds" % (h.get("quelle"), h.get("alter_s", 0))


# --- Befehle ----------------------------------------------------------

def befehl_status(args):
    _kopf("KRYPTO - SYSTEMSTATUS")
    for k, v in konfig.zusammenfassung().items():
        print("%-24s %s" % (k, v))
    _linie()
    bremse = wache.notbremse_stand()
    print("Notbremse                %s" % (
        "GEZOGEN: %s (%s)" % (bremse["text"], bremse["zeit"])
        if bremse else "frei"))
    zustand = tor.live_zustand()
    print("Live-Handel              GESPERRT")
    for f in zustand["fehlt"]:
        print("   offen: %s" % f)
    _linie()
    d = papier.Depot.laden()
    k = d.kennzahlen()
    print("Papierdepot              %.2f %s (Start %.2f, %+.2f %%)"
          % (k["gesamtwert"], konfig.WAEHRUNG.upper(), k["kapital_start"],
             k["rendite"] * 100))
    print("Offene Positionen        %d" % k["offene_positionen"])
    print("Abgeschlossene Trades    %d" % k["abgeschlossen"])
    return 0


def befehl_health(args):
    _kopf("KRYPTO - GESUNDHEIT")
    ok = True

    erreichbar = quelle.erreichbar()
    print("Datenquelle CoinGecko    %s" % ("erreichbar" if erreichbar
                                           else "NICHT ERREICHBAR"))
    ok = ok and erreichbar
    if not erreichbar:
        wache.fehler_melden("api")

    try:
        kerzen, h = quelle.kerzen("bitcoin", tage=30)
        from krypto.daten import pruefung
        befund = pruefung.kerzen_pruefen(kerzen, konfig.MIN_KERZEN,
                                         konfig.DATEN_MAX_ALTER_S)
        print("Kerzen BTC               %d Stueck (%s)"
              % (len(kerzen), _herkunft(h)))
        print("Datenpruefung            %s" % befund.bericht())
        ok = ok and bool(befund)
    except quelle.DatenFehler as e:
        print("Kerzen BTC               FEHLER: %s" % e)
        ok = False

    bremse = wache.notbremse_stand()
    print("Notbremse                %s" % ("GEZOGEN" if bremse else "frei"))
    ok = ok and not bremse

    print("Live-Handel              GESPERRT (gewollt)")
    print("Protokollverzeichnis     %s" % konfig.LOGS)
    _linie()
    print("GESAMT                   %s" % ("OK" if ok else "NICHT OK"))
    protokoll.system("gesundheit", ok=ok)
    return 0 if ok else 1


def befehl_scan(args):
    _kopf("KRYPTO - MARKTSCAN")
    zugelassen, abgelehnt, h = universum.aufbauen(anzahl=args.anzahl)
    print("Quelle: CoinGecko (%s), %d Werte geprueft\n"
          % (_herkunft(h), len(zugelassen) + len(abgelehnt)))
    print("%-6s %14s %16s %16s %8s" % ("Wert", "Kurs", "Volumen 24h",
                                       "Marktkapital", "24h %"))
    _linie()
    for k in zugelassen:
        print("%-6s %14.4f %16.0f %16.0f %8s"
              % (k.symbol.upper(), k.kurs, k.volumen, k.marktkapital,
                 ("%+.1f" % k.aend_24h) if k.aend_24h is not None else "-"))
    print("\nZugelassen: %d   Abgelehnt: %d" % (len(zugelassen), len(abgelehnt)))
    if args.ausfuehrlich:
        print("\nAbgelehnt, mit Grund:")
        for k in abgelehnt:
            print("  %-6s %s" % (k.symbol.upper(),
                                 "; ".join(k.befund.gruende)[:80]))
    return 0


def befehl_watchlist(args):
    _kopf("KRYPTO - BEOBACHTUNGSLISTE")
    zugelassen, _, h = universum.aufbauen(anzahl=args.anzahl)
    liste = zugelassen[:args.top]
    print("Quelle: CoinGecko (%s)\n" % _herkunft(h))
    for i, k in enumerate(liste, 1):
        u = k.umschlag
        print("%2d. %-6s %-18s Kurs %12.4f  Umschlag %s"
              % (i, k.symbol.upper(), (k.name or "")[:18], k.kurs,
                 ("%.3f" % u) if u is not None else "-"))
    protokoll.markt("watchlist", werte=[k.id for k in liste])
    return 0


def _bewerten_eine(kandidat_oder_id, kandidat=None, tage=30):
    coin_id = getattr(kandidat_oder_id, "id", kandidat_oder_id)
    kerzen, h = quelle.kerzen(coin_id, tage=tage)
    b = bw.bewerten(kerzen, kandidat=kandidat)
    return b, kerzen, h


def befehl_research(args):
    _kopf("KRYPTO - RECHERCHE: %s" % args.coin.upper())
    try:
        b, kerzen, h = _bewerten_eine(args.coin, tage=args.tage)
    except quelle.DatenFehler as e:
        print("NICHT VERFUEGBAR: %s" % e)
        return 1

    print("Datenquelle              CoinGecko (%s)" % _herkunft(h))
    print("Kerzen                   %d" % len(kerzen))
    print("Datenpruefung            %s\n" % b.datenbefund.bericht())

    print("INDIKATOREN")
    for name, schluessel in (("Kurs", "kurs"), ("EMA 12", "ema12"),
                             ("EMA 26", "ema26"), ("EMA 50", "ema50"),
                             ("RSI 14", "rsi14"), ("MACD-Hist", "macd_hist"),
                             ("ATR 14", "atr14"), ("ATR in %", "atr_anteil"),
                             ("Volatilitaet", "vola20")):
        v = b.werte.get(schluessel)
        if v is None:
            print("  %-16s NICHT BERECHENBAR" % name)
        elif schluessel in ("atr_anteil", "vola20"):
            print("  %-16s %.2f %%" % (name, v * 100))
        else:
            print("  %-16s %.4f" % (name, v))
    print("  %-16s %s" % ("Regime", b.werte.get("regime")))
    print("  %-16s %s" % ("Widerstand", b.werte.get("widerstand")))
    print("  %-16s %s" % ("Unterstuetzung", b.werte.get("unterstuetzung")))

    print("\nBEWERTUNG")
    print("  Chance                 %.0f / 100 (Schwelle %.0f)"
          % (b.chance, konfig.CHANCE_SCHWELLE))
    print("  Risiko                 %.0f / 100 (Grenze %.0f)"
          % (b.risiko, konfig.RISIKO_SCHWELLE))
    print("  ENTSCHEID              %s" % b.entscheid)
    for g in b.gruende:
        print("    +  %s" % g)
    for g in b.hinweise:
        print("    ~  %s  (Risikopunkte, kein Verbot)" % g)
    for g in b.blocker:
        print("    !  %s  (VETO)" % g)

    stop, ziel = bw.stop_und_ziel(b.werte.get("kurs"), b.werte.get("atr14"))
    if stop:
        d = papier.Depot.laden()
        g = groesse.berechnen(d.gesamtwert(), d.geld, b.werte["kurs"], stop)
        print("\nHYPOTHETISCHE ORDER (nichts wird gestellt)")
        print("  Einstieg %.4f  Stop %.4f  Ziel %.4f"
              % (b.werte["kurs"], stop, ziel))
        print("  Menge %.6f  Gegenwert %.2f  Risiko %.2f"
              % (g.menge, g.wert, g.risiko_geld))
        for r in g.gruende:
            print("    - %s" % r)
    protokoll.signal("recherche", coin=args.coin, entscheid=b.entscheid,
                     chance=b.chance, risiko=b.risiko)
    return 0


def befehl_signals(args):
    _kopf("KRYPTO - SIGNALE")
    zugelassen, _, h = universum.aufbauen(anzahl=args.anzahl)
    liste = zugelassen[:args.top]
    print("Quelle: CoinGecko (%s), %d Werte\n" % (_herkunft(h), len(liste)))
    print("%-8s %-9s %7s %7s  %s" % ("Wert", "Entscheid", "Chance",
                                     "Risiko", "Begruendung"))
    _linie()
    treffer = 0
    for k in liste:
        try:
            b, _, _ = _bewerten_eine(k, kandidat=k, tage=args.tage)
        except quelle.DatenFehler as e:
            print("%-8s %-9s %7s %7s  %s"
                  % (k.symbol.upper(), "KEINE DATEN", "-", "-", str(e)[:40]))
            continue
        if b.entscheid == "TRADE":
            treffer += 1
        print("%-8s %-9s %7.0f %7.0f  %s"
              % (k.symbol.upper(), b.entscheid, b.chance, b.risiko,
                 "; ".join(b.blocker or b.gruende)[:44]))
        protokoll.signal("bewertung", coin=k.id, entscheid=b.entscheid,
                         chance=b.chance, risiko=b.risiko)
    _linie()
    print("TRADE-Signale: %d von %d" % (treffer, len(liste)))
    print("Ein Signal ist keine Prognose. Es ist eine Bedingungslage.")
    return 0


def befehl_risk(args):
    _kopf("KRYPTO - RISIKOLAGE")
    d = papier.Depot.laden()
    k = d.kennzahlen()
    gesamt = k["gesamtwert"]
    investiert = sum(p.wert() for p in d.positionen.values())

    def zeile(name, ist, grenze, einheit="%"):
        anteil = (ist / grenze * 100) if grenze else 0
        markierung = "  <-- ERREICHT" if anteil >= 100 else ""
        print("%-26s %8.2f %s  von %8.2f %s%s"
              % (name, ist, einheit, grenze, einheit, markierung))

    print("Depotwert                  %.2f %s"
          % (gesamt, konfig.WAEHRUNG.upper()))
    print("Davon investiert           %.2f (%.1f %%)"
          % (investiert, investiert / gesamt * 100 if gesamt else 0))
    _linie()
    zeile("Exposure", investiert / gesamt * 100 if gesamt else 0,
          konfig.EXPOSURE_MAX * 100)
    zeile("Drawdown", d.drawdown() * 100, konfig.DRAWDOWN_MAX * 100)
    tag = d.tagesergebnis()
    zeile("Tagesverlust",
          max(0.0, -tag / d.kapital_tagesbeginn * 100)
          if d.kapital_tagesbeginn else 0, konfig.VERLUST_TAG_MAX * 100)
    zeile("Offene Positionen", len(d.positionen), konfig.POSITIONEN_MAX, "St")
    zeile("Trades heute", d.trades_heute(), konfig.TRADES_TAG_MAX, "St")
    _linie()
    bremse = wache.notbremse_stand()
    print("Notbremse: %s" % ("GEZOGEN - %s (%s)"
                             % (bremse["text"], bremse["zeit"])
                             if bremse else "frei"))
    if d.positionen:
        print("\nPositionen:")
        for p in d.positionen.values():
            print("  %-8s Menge %.6f  Einstieg %.4f  Stop %s  Ziel %s  P/L %+.2f"
                  % (p.symbol, p.menge, p.einstieg,
                     "%.4f" % p.stop if p.stop else "FEHLT",
                     "%.4f" % p.ziel if p.ziel else "-", p.ergebnis()))
    return 0


def befehl_positions(args):
    _kopf("KRYPTO - POSITIONEN (Papier)")
    d = papier.Depot.laden()
    if not d.positionen:
        print("Keine offenen Positionen.")
        return 0
    for p in d.positionen.values():
        print("%-8s Menge %.6f  Einstieg %.4f  Kurs %.4f  P/L %+.2f (%+.2f %%)"
              % (p.symbol, p.menge, p.einstieg, p.letzter_kurs, p.ergebnis(),
                 (p.letzter_kurs / p.einstieg - 1) * 100))
        print("         Stop %s  Ziel %s  eroeffnet %s"
              % ("%.4f" % p.stop if p.stop else "FEHLT",
                 "%.4f" % p.ziel if p.ziel else "-", p.eroeffnet))
    return 0


def befehl_performance(args):
    _kopf("KRYPTO - ERGEBNIS (Papier)")
    d = papier.Depot.laden()
    k = d.kennzahlen()
    for name, wert, form in (
            ("Startkapital", k["kapital_start"], "%.2f"),
            ("Depotwert heute", k["gesamtwert"], "%.2f"),
            ("Rendite", k["rendite"] * 100, "%+.2f %%"),
            ("Abgeschlossene Trades", k["abgeschlossen"], "%d"),
            ("Treffer", k["treffer"], "%d"),
            ("Gebuehren gesamt", k["gebuehren_gesamt"], "%.2f"),
            ("Hoechststand", k["hoechststand"], "%.2f"),
            ("Drawdown jetzt", k["drawdown_jetzt"] * 100, "%.2f %%")):
        print("%-24s " % name + (form % wert))
    tq = k["trefferquote"]
    print("%-24s %s" % ("Trefferquote",
                        ("%.1f %%" % (tq * 100)) if tq is not None
                        else "NICHT BERECHENBAR (keine abgeschlossenen Trades)"))
    pf = k["profitfaktor"]
    print("%-24s %s" % ("Profitfaktor",
                        ("%.2f" % pf) if isinstance(pf, float)
                        and pf != float("inf") else
                        ("unendlich (kein Verlusttrade)" if pf else
                         "NICHT BERECHENBAR")))
    if k["abgeschlossen"] < 30:
        print("\nHinweis: %d Trades sind zu wenig fuer eine belastbare "
              "Aussage. Unter etwa 30 Trades ist jede Kennzahl Zufall."
              % k["abgeschlossen"])
    return 0


def befehl_backtest(args):
    _kopf("KRYPTO - BACKTEST: %s" % args.coin.upper())
    try:
        kerzen, h = quelle.kerzen(args.coin, tage=args.tage)
    except quelle.DatenFehler as e:
        print("NICHT VERFUEGBAR: %s" % e)
        return 1
    print("Kerzen %d (%s)" % (len(kerzen), _herkunft(h)))
    if len(kerzen) < konfig.MIN_KERZEN + 10:
        print("ZU WENIG DATEN fuer einen Backtest "
              "(%d Kerzen, mindestens %d noetig)."
              % (len(kerzen), konfig.MIN_KERZEN + 10))
        return 1

    e = motor.laufen(kerzen, symbol=args.coin.upper())
    b = e.bericht()
    _linie()
    for name, schluessel, form in (
            ("Kapital Start", "kapital_start", "%.2f"),
            ("Kapital Ende", "kapital_ende", "%.2f"),
            ("Rendite", "rendite", None),
            ("Trades", "trades", "%d"),
            ("Trefferquote", "trefferquote", None),
            ("Profitfaktor", "profitfaktor", None),
            ("Max. Drawdown", "max_drawdown", None),
            ("Sharpe", "sharpe", None),
            ("Gebuehren", "gebuehren_gesamt", "%.2f"),
            ("Signale TRADE", "signale_trade", "%d"),
            ("Signale gesamt", "signale_gesamt", "%d")):
        v = b[schluessel]
        if v is None:
            print("%-22s NICHT BERECHENBAR" % name)
        elif form:
            print("%-22s " % name + form % v)
        elif schluessel in ("rendite", "max_drawdown", "trefferquote"):
            print("%-22s %+.2f %%" % (name, v * 100))
        else:
            print("%-22s %.2f" % (name, v))
    vergleich = motor.kaufen_und_halten(kerzen)
    if vergleich is not None:
        print("%-22s %+.2f %%  (nach Kosten)"
              % ("Kaufen und halten", vergleich * 100))
        besser = b["rendite"] > vergleich
        print("\nDas System war %s als einfach kaufen und halten."
              % ("besser" if besser else "SCHLECHTER"))
    _linie()
    print("Ein Backtest ueber %d Kerzen und %d Trades beweist nichts."
          % (b["kerzen"], b["trades"]))
    print("Er zeigt nur, dass die Mechanik rechnet - nicht, dass sie "
          "verdient.")
    protokoll.system("backtest", **b)
    return 0


def befehl_paper(args):
    _kopf("KRYPTO - PAPIERHANDEL")
    d = papier.Depot.laden()

    if args.zuruecksetzen:
        d = papier.Depot()
        d.speichern()
        print("Papierdepot zurueckgesetzt auf %.2f %s."
              % (d.kapital_start, konfig.WAEHRUNG.upper()))
        protokoll.trade("depot-zurueckgesetzt", kapital=d.kapital_start)
        return 0

    zugelassen, _, h = universum.aufbauen(anzahl=args.anzahl)
    liste = zugelassen[:args.top]
    print("Quelle: CoinGecko (%s)\n" % _herkunft(h))

    # 1. Kurse der offenen Positionen nachfuehren, Stops pruefen.
    kurse = {k.symbol.upper(): k.kurs for k in zugelassen}
    ausgeloest = d.kurse_setzen({s: p for s, p in kurse.items()
                                 if s in d.positionen})
    for a in ausgeloest:
        print("AUSGELOEST  %s %s bei %.4f -> %+.2f"
              % (a["grund"], a["symbol"], a["kurs"], a["ergebnis"]))

    # 2. Neue Signale pruefen.
    for k in liste:
        symbol = k.symbol.upper()
        if symbol in d.positionen:
            continue
        try:
            b, kerzen, _ = _bewerten_eine(k, kandidat=k, tage=30)
        except quelle.DatenFehler as e:
            print("%-8s keine Daten: %s" % (symbol, str(e)[:50]))
            continue
        if b.entscheid != "TRADE":
            print("%-8s NO TRADE  %s" % (symbol,
                                         b.kurzbegruendung()[:52]))
            continue
        stop, ziel = bw.stop_und_ziel(k.kurs, b.werte.get("atr14"))
        g = groesse.berechnen(d.gesamtwert(), d.geld, k.kurs, stop)
        pruef = wache.order_pruefen(d, symbol, k.kurs, stop, g.menge)
        if not pruef:
            print("%-8s ABGELEHNT %s" % (symbol, "; ".join(pruef.gruende)[:52]))
            continue
        if args.trocken:
            print("%-8s WUERDE KAUFEN Menge %.6f zu %.4f (Trockenlauf)"
                  % (symbol, g.menge, k.kurs))
            continue
        d.kaufen(symbol, g.menge, k.kurs, stop, ziel,
                 grund="Chance %.0f Risiko %.0f" % (b.chance, b.risiko))
        print("%-8s GEKAUFT   Menge %.6f zu %.4f, Stop %.4f, Ziel %.4f"
              % (symbol, g.menge, k.kurs, stop, ziel))

    d.speichern()
    k = d.kennzahlen()
    _linie()
    print("Depotwert %.2f  Geld %.2f  Positionen %d"
          % (k["gesamtwert"], k["geld"], k["offene_positionen"]))
    print("Kein echtes Geld bewegt. Live-Handel ist gesperrt.")
    return 0


def befehl_kill(args):
    if args.loesen:
        if wache.notbremse_loesen():
            print("Notbremse geloest.")
        else:
            print("Es war keine Notbremse gezogen.")
        return 0
    stand = wache.notbremse_ziehen("hand", args.grund or "")
    print("NOTBREMSE GEZOGEN: %s" % stand["text"])
    print("Es werden keine neuen Positionen mehr eroeffnet.")
    print("Offene Positionen bleiben bestehen - sie muessen von Hand "
          "geschlossen werden:")
    print("  python3 -m krypto.cli verkaufen SYMBOL")
    print("Loesen mit: python3 -m krypto.cli kill --loesen")
    return 0


def befehl_verkaufen(args):
    d = papier.Depot.laden()
    if args.symbol not in d.positionen:
        print("Keine Position in %s." % args.symbol)
        return 1
    try:
        kerzen, _ = quelle.kerzen(args.coin or args.symbol.lower(), tage=1)
        kurs = kerzen[-1][4]
    except quelle.DatenFehler:
        kurs = d.positionen[args.symbol].letzter_kurs
        print("Kein frischer Kurs - es wird mit dem letzten bekannten "
              "gerechnet (%.4f). Die Zahl ist NICHT taktuell." % kurs)
    e = d.verkaufen(args.symbol, kurs, grund="von Hand")
    d.speichern()
    print("Verkauft: %s zu %.4f, Ergebnis %+.2f" % (e["symbol"], e["kurs"],
                                                    e["ergebnis"]))
    return 0


def befehl_logs(args):
    _kopf("KRYPTO - PROTOKOLL: %s" % args.spur)
    for e in protokoll.lesen(args.spur, tage=args.tage, grenze=args.anzahl):
        print(json.dumps(e, ensure_ascii=False))
    return 0


# --- Einstieg ---------------------------------------------------------

def bauen():
    p = argparse.ArgumentParser(
        prog="krypto", description="Krypto-Analyse und Papierhandel. "
                                   "Stellt keine echten Orders.")
    u = p.add_subparsers(dest="befehl", required=True)

    u.add_parser("status", help="Konfiguration und Depot").set_defaults(
        f=befehl_status)
    u.add_parser("health", help="Datenquelle und Systemzustand").set_defaults(
        f=befehl_health)

    s = u.add_parser("scan", help="Marktscan mit Liquiditaetsfilter")
    s.add_argument("--anzahl", type=int, default=50)
    s.add_argument("--ausfuehrlich", action="store_true")
    s.set_defaults(f=befehl_scan)

    w = u.add_parser("watchlist", help="Beobachtungsliste")
    w.add_argument("--anzahl", type=int, default=50)
    w.add_argument("--top", type=int, default=10)
    w.set_defaults(f=befehl_watchlist)

    r = u.add_parser("research", help="Ein Wert im Detail")
    r.add_argument("coin", help="CoinGecko-Kennung, z.B. bitcoin")
    r.add_argument("--tage", type=int, default=30)
    r.set_defaults(f=befehl_research)

    g = u.add_parser("signals", help="Signale ueber die Watchlist")
    g.add_argument("--anzahl", type=int, default=50)
    g.add_argument("--top", type=int, default=8)
    g.add_argument("--tage", type=int, default=30)
    g.set_defaults(f=befehl_signals)

    u.add_parser("risk", help="Risikolage und Grenzen").set_defaults(
        f=befehl_risk)
    u.add_parser("positions", help="Offene Papierpositionen").set_defaults(
        f=befehl_positions)
    u.add_parser("performance", help="Ergebnis des Papierdepots").set_defaults(
        f=befehl_performance)

    b = u.add_parser("backtest", help="Backtest auf echten Kerzen")
    b.add_argument("coin")
    b.add_argument("--tage", type=int, default=30)
    b.set_defaults(f=befehl_backtest)

    pa = u.add_parser("paper", help="Papierhandel ausfuehren")
    pa.add_argument("--anzahl", type=int, default=50)
    pa.add_argument("--top", type=int, default=8)
    pa.add_argument("--trocken", action="store_true",
                    help="nur zeigen, was passieren wuerde")
    pa.add_argument("--zuruecksetzen", action="store_true")
    pa.set_defaults(f=befehl_paper)

    v = u.add_parser("verkaufen", help="Papierposition schliessen")
    v.add_argument("symbol")
    v.add_argument("--coin", help="CoinGecko-Kennung, falls abweichend")
    v.set_defaults(f=befehl_verkaufen)

    ki = u.add_parser("kill", help="Notbremse ziehen oder loesen")
    ki.add_argument("--loesen", action="store_true")
    ki.add_argument("--grund", default="")
    ki.set_defaults(f=befehl_kill)

    lo = u.add_parser("logs", help="Protokoll lesen")
    lo.add_argument("spur", choices=protokoll.SPUREN)
    lo.add_argument("--tage", type=int, default=1)
    lo.add_argument("--anzahl", type=int, default=40)
    lo.set_defaults(f=befehl_logs)

    return p


def main(argv=None):
    args = bauen().parse_args(argv)
    try:
        return args.f(args)
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
        return 130
    except quelle.DatenFehler as e:
        print("DATEN NICHT VERFUEGBAR: %s" % e)
        protokoll.fehler("cli-datenfehler", befehl=args.befehl, grund=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
