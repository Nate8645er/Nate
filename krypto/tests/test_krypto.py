# KRYPTO - Tests.
#
#   python3 -m krypto.tests.test_krypto
#
# Kein Test hier ruft das Netz. Getestet wird das, was ueber Geld
# entscheidet: Indikatoren gegen von Hand nachgerechnete Werte, die
# Risikogrenzen gegen genau die Faelle, die sie verhindern sollen, und
# der Backtest gegen den Fehler, der jeden Backtest wertlos macht -
# den Blick in die Zukunft.

import math
import os
import tempfile
import time
import unittest

from krypto import konfig
from krypto.analyse import bewertung as bw
from krypto.analyse import indikatoren as ind
from krypto.backtest import motor
from krypto.betrieb import protokoll
from krypto.daten import pruefung
from krypto.handel import papier, tor
from krypto.risiko import groesse, wache

STUNDE = 3600_000


def kerzen_bauen(schlusskurse, start=None, takt=4 * STUNDE, spanne=0.01):
    """Baut aus Schlusskursen eine gueltige OHLC-Reihe."""
    if start is None:
        start = int(time.time() * 1000) - len(schlusskurse) * takt
    raus = []
    vorher = schlusskurse[0]
    for i, c in enumerate(schlusskurse):
        o = vorher
        h = max(o, c) * (1 + spanne)
        t = min(o, c) * (1 - spanne)
        raus.append([start + i * takt, o, h, t, c])
        vorher = c
    return raus


def echter_aufwaertstrend(n=220, steigung=0.003, welle=0.05):
    """Aufwaertstrend MIT Ruecksetzern.

    Ein reiner Exponentialtrend taugt nicht als Testfall: er haelt den
    RSI dauerhaft bei 100, und das System lehnt dann - korrekt - jeden
    Einstieg als ueberkauft ab. Echte Maerkte atmen. Diese Reihe auch.
    """
    return [100 * (1 + steigung) ** i * (1 + welle * math.sin(i / 7.0))
            for i in range(n)]


class IndikatorTest(unittest.TestCase):

    def test_sma_von_hand(self):
        self.assertEqual(ind.sma([1, 2, 3, 4, 5], 3), [None, None, 2.0, 3.0, 4.0])

    def test_ema_startet_mit_sma(self):
        e = ind.ema([1, 2, 3, 4, 5], 3)
        self.assertIsNone(e[1])
        self.assertAlmostEqual(e[2], 2.0)          # SMA(1,2,3)
        self.assertAlmostEqual(e[3], (4 - 2) * 0.5 + 2)   # Faktor 2/(3+1)

    def test_rsi_nur_gewinne_ist_hundert(self):
        r = ind.rsi(list(range(1, 40)), 14)
        self.assertAlmostEqual(r[-1], 100.0)

    def test_rsi_nur_verluste_ist_null(self):
        r = ind.rsi(list(range(40, 1, -1)), 14)
        self.assertAlmostEqual(r[-1], 0.0)

    def test_rsi_bleibt_im_band(self):
        werte = [100 + (i % 7) * 3 - (i % 5) * 2 for i in range(120)]
        for x in ind.rsi(werte, 14):
            if x is not None:
                self.assertGreaterEqual(x, 0.0)
                self.assertLessEqual(x, 100.0)

    def test_reihen_sind_gleich_lang(self):
        """Der Schutz gegen versehentliches Verschieben der Reihen."""
        w = [100 + i for i in range(80)]
        for reihe in (ind.sma(w, 20), ind.ema(w, 20), ind.rsi(w, 14),
                      ind.volatilitaet(w, 20)):
            self.assertEqual(len(reihe), len(w))
        m, s, h = ind.macd(w)
        self.assertEqual((len(m), len(s), len(h)), (len(w), len(w), len(w)))

    def test_macd_signal_startet_nach_macd(self):
        w = [100 + i * 0.5 for i in range(80)]
        m, s, _ = ind.macd(w)
        erst_m = next(i for i, x in enumerate(m) if x is not None)
        erst_s = next(i for i, x in enumerate(s) if x is not None)
        self.assertGreater(erst_s, erst_m)

    def test_atr_bei_konstanter_spanne(self):
        hoch = [110.0] * 30
        tief = [100.0] * 30
        schluss = [105.0] * 30
        a = ind.atr(hoch, tief, schluss, 14)
        self.assertAlmostEqual(a[-1], 10.0)

    def test_marken_sehen_nicht_in_die_zukunft(self):
        """Eine Marke am rechten Rand waere ein Blick nach vorn."""
        hoch = [10, 11, 12, 13, 14, 15, 14, 13, 12, 11, 10, 30]
        tief = [h - 2 for h in hoch]
        m = ind.marken(hoch, tief, fenster=5)
        self.assertNotIn(30, m["widerstand"])

    def test_periode_null_wird_abgelehnt(self):
        with self.assertRaises(ValueError):
            ind.sma([1, 2, 3], 0)


class DatenpruefungTest(unittest.TestCase):

    def test_gute_reihe_ist_tauglich(self):
        k = kerzen_bauen([100 + i for i in range(80)])
        self.assertTrue(pruefung.kerzen_pruefen(k, 60, 86400))

    def test_zu_wenige_kerzen(self):
        k = kerzen_bauen([100 + i for i in range(10)])
        b = pruefung.kerzen_pruefen(k, 60, 86400)
        self.assertFalse(b)
        self.assertIn("nur 10 Kerzen", b.bericht())

    def test_alte_daten_werden_abgelehnt(self):
        alt = int(time.time() * 1000) - 400 * 86400_000
        k = kerzen_bauen([100 + i for i in range(80)], start=alt)
        self.assertFalse(pruefung.kerzen_pruefen(k, 60, 3600))

    def test_altersgrenze_folgt_dem_kerzentakt(self):
        """Bei 4-Stunden-Kerzen ist eine 150 Minuten alte letzte Kerze
        normal, nicht veraltet. Eine feste 1-Stunden-Grenze wuerde hier
        jede echte CoinGecko-Reihe verwerfen - genau das ist beim ersten
        Lauf gegen die echte Quelle passiert."""
        jetzt = time.time()
        start = int((jetzt - 150 * 60) * 1000) - 79 * 4 * STUNDE
        k = kerzen_bauen([100 + i for i in range(80)], start=start,
                         takt=4 * STUNDE)
        self.assertTrue(pruefung.kerzen_pruefen(k, 60, 3600, jetzt=jetzt))

    def test_deutlich_ueberfaellige_kerze_wird_abgelehnt(self):
        """Drei Takte ohne neue Kerze sind kein Takt mehr, sondern ein
        Ausfall."""
        jetzt = time.time()
        start = int((jetzt - 13 * 3600) * 1000) - 79 * 4 * STUNDE
        k = kerzen_bauen([100 + i for i in range(80)], start=start,
                         takt=4 * STUNDE)
        b = pruefung.kerzen_pruefen(k, 60, 3600, jetzt=jetzt)
        self.assertFalse(b)
        self.assertTrue(any("Kerzentakt" in g for g in b.gruende))

    def test_zeitstempel_muessen_steigen(self):
        k = kerzen_bauen([100 + i for i in range(80)])
        k[40][0], k[41][0] = k[41][0], k[40][0]
        b = pruefung.kerzen_pruefen(k, 60, 86400)
        self.assertFalse(b)
        self.assertTrue(any("aufsteigend" in g for g in b.gruende))

    def test_widerspruechliche_kerze(self):
        k = kerzen_bauen([100 + i for i in range(80)])
        k[30][2] = k[30][3] - 1        # Hoch unter Tief
        self.assertFalse(pruefung.kerzen_pruefen(k, 60, 86400))

    def test_negativer_kurs(self):
        k = kerzen_bauen([100 + i for i in range(80)])
        k[10][4] = -5
        self.assertFalse(pruefung.kerzen_pruefen(k, 60, 86400))

    def test_markteintrag_zu_klein(self):
        b = pruefung.markteintrag_pruefen(
            {"current_price": 1.0, "total_volume": 1000, "market_cap": 2000},
            50_000_000, 500_000_000)
        self.assertFalse(b)
        self.assertEqual(len(b.gruende), 2)


class BewertungTest(unittest.TestCase):

    def test_zu_wenig_daten_ist_no_trade(self):
        k = kerzen_bauen([100] * 10)
        b = bw.bewerten(k, daten_pruefen=False)
        self.assertEqual(b.entscheid, "NO TRADE")

    def test_klarer_aufwaertstrend_gibt_hohe_chance(self):
        k = kerzen_bauen([100 * (1.004 ** i) for i in range(120)])
        b = bw.bewerten(k, daten_pruefen=False)
        self.assertGreaterEqual(b.chance, 60)

    def test_abwaertstrend_ist_no_trade(self):
        k = kerzen_bauen([200 * (0.99 ** i) for i in range(120)])
        b = bw.bewerten(k, daten_pruefen=False)
        self.assertEqual(b.entscheid, "NO TRADE")

    def test_risikonotiz_ist_kein_veto(self):
        """Regression. Beim ersten Lauf gegen echte Daten wurde BNB mit
        Chance 80 und Risiko 34 abgelehnt - allein wegen eines niedrigen
        Umschlags. Damit war der Risiko-Score wirkungslos: jede Notiz
        wirkte wie ein Verbot. Risikopunkte und Vetos sind getrennt."""

        class Kandidat:
            befund = pruefung.Befund(True)
            umschlag = 0.005              # niedrig, aber bei BTC normal

        k = kerzen_bauen(echter_aufwaertstrend())
        ohne = bw.bewerten(k, daten_pruefen=False)
        mit = bw.bewerten(k, kandidat=Kandidat(), daten_pruefen=False)
        self.assertEqual(mit.entscheid, ohne.entscheid)
        self.assertIn("Umschlag unter 2 % des Marktkapitals", mit.hinweise)
        self.assertNotIn("Umschlag unter 2 % des Marktkapitals", mit.blocker)

    def test_zu_wenig_liquiditaet_ist_ein_veto(self):
        class Schwach:
            befund = pruefung.Befund(False, ["Volumen zu klein"])
            umschlag = 0.5

        b = bw.bewerten(kerzen_bauen(echter_aufwaertstrend()),
                        kandidat=Schwach(), daten_pruefen=False)
        self.assertEqual(b.entscheid, "NO TRADE")
        self.assertTrue(any("Liquiditaet" in g for g in b.blocker))

    def test_stop_liegt_unter_einstieg(self):
        stop, ziel = bw.stop_und_ziel(100.0, 2.0)
        self.assertLess(stop, 100.0)
        self.assertGreater(ziel, 100.0)

    def test_ohne_atr_kein_stop(self):
        self.assertEqual(bw.stop_und_ziel(100.0, None), (None, None))
        self.assertEqual(bw.stop_und_ziel(100.0, 0), (None, None))

    def test_zu_grosser_atr_gibt_keinen_stop_unter_null(self):
        self.assertEqual(bw.stop_und_ziel(10.0, 100.0), (None, None))


class GroessenTest(unittest.TestCase):

    def test_menge_folgt_aus_dem_stopabstand(self):
        # max_anteil=1.0 schaltet den Positionsdeckel ab, damit hier
        # wirklich nur die Formel geprueft wird. Dass der Deckel sonst
        # greift, prueft test_positionsdeckel_greift.
        g = groesse.berechnen(10000, 10000, 100.0, 98.0,
                              risiko_anteil=0.01, max_anteil=1.0)
        self.assertAlmostEqual(g.menge, 50.0)          # 100 Risiko / 2 Abstand
        self.assertAlmostEqual(g.risiko_geld, 100.0)

    def test_deckel_greift_auch_bei_normalem_stop(self):
        """Mit den echten Vorgaben bindet der 20-%-Deckel, nicht die
        Risikoformel - genau so soll es sein."""
        g = groesse.berechnen(10000, 10000, 100.0, 98.0)
        self.assertAlmostEqual(g.wert, 2000.0)
        self.assertEqual(g.begrenzt_durch,
                         "Positionsdeckel 20 % des Kapitals")

    def test_ohne_stop_keine_menge(self):
        self.assertEqual(groesse.berechnen(10000, 10000, 100.0, None).menge, 0)

    def test_stop_ueber_einstieg_wird_abgelehnt(self):
        self.assertEqual(groesse.berechnen(10000, 10000, 100.0, 101.0).menge, 0)

    def test_positionsdeckel_greift(self):
        # Enger Stop wuerde 1000 Stueck ergeben - der Deckel von 20 %
        # laesst nur 20 Stueck zu.
        g = groesse.berechnen(10000, 10000, 100.0, 99.9,
                              risiko_anteil=0.01, max_anteil=0.20)
        self.assertAlmostEqual(g.wert, 2000.0, places=2)

    def test_freies_geld_begrenzt(self):
        g = groesse.berechnen(10000, 500, 100.0, 98.0)
        self.assertLessEqual(g.wert, 500.0)


class DepotTest(unittest.TestCase):

    def test_kauf_kostet_gebuehr_und_slippage(self):
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 98.0, 106.0)
        self.assertLess(d.geld, 9900.0)             # 100 + Gebuehr + Slippage
        self.assertIn("BTC", d.positionen)

    def test_kein_kauf_ohne_geld(self):
        d = papier.Depot(kapital=100)
        with self.assertRaises(ValueError):
            d.kaufen("BTC", 10.0, 100.0, 98.0, 106.0)

    def test_keine_doppelte_position(self):
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 98.0, 106.0)
        with self.assertRaises(ValueError):
            d.kaufen("BTC", 1.0, 100.0, 98.0, 106.0)

    def test_stop_greift_am_tief_nicht_am_schluss(self):
        """Der teuerste Rechenfehler im Backtest: der Stop wird
        innerhalb der Kerze gerissen, aber der Schlusskurs liegt wieder
        darueber. Wer nur den Schluss prueft, unterschlaegt den
        Verlust."""
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 95.0, 110.0)
        ausgeloest = d.kurse_setzen({"BTC": 101.0}, kerze={"BTC": (102.0, 94.0)})
        self.assertEqual(len(ausgeloest), 1)
        self.assertEqual(ausgeloest[0]["grund"], "stop-loss")
        self.assertNotIn("BTC", d.positionen)

    def test_bei_stop_und_ziel_in_einer_kerze_gilt_der_stop(self):
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 95.0, 105.0)
        a = d.kurse_setzen({"BTC": 100.0}, kerze={"BTC": (106.0, 94.0)})
        self.assertEqual(a[0]["grund"], "stop-loss")

    def test_take_profit(self):
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 95.0, 105.0)
        a = d.kurse_setzen({"BTC": 106.0}, kerze={"BTC": (106.0, 99.0)})
        self.assertEqual(a[0]["grund"], "take-profit")
        self.assertGreater(a[0]["ergebnis"], 0)

    def test_kennzahlen_ohne_trades_erfinden_nichts(self):
        k = papier.Depot(kapital=10000).kennzahlen()
        self.assertIsNone(k["trefferquote"])
        self.assertIsNone(k["profitfaktor"])

    def test_speichern_und_laden(self):
        d = papier.Depot(kapital=10000)
        d.kaufen("BTC", 1.0, 100.0, 98.0, 106.0)
        with tempfile.TemporaryDirectory() as ordner:
            p = os.path.join(ordner, "depot.json")
            d.speichern(p)
            neu = papier.Depot.laden(p)
        self.assertAlmostEqual(neu.geld, d.geld)
        self.assertEqual(list(neu.positionen), ["BTC"])
        self.assertAlmostEqual(neu.positionen["BTC"].einstieg,
                               d.positionen["BTC"].einstieg)

    def test_laden_ohne_datei_gibt_frisches_depot(self):
        d = papier.Depot.laden("/nicht/vorhanden/depot.json")
        self.assertEqual(d.geld, d.kapital_start)


class RisikoTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.TemporaryDirectory()
        self._bremse, wache.NOTBREMSE = wache.NOTBREMSE, \
            os.path.join(self.ordner.name, "notbremse.json")
        self._zaehler, wache._ZAEHLER = wache._ZAEHLER, \
            os.path.join(self.ordner.name, "zaehler.json")

    def tearDown(self):
        wache.NOTBREMSE, wache._ZAEHLER = self._bremse, self._zaehler
        self.ordner.cleanup()

    def _depot(self):
        return papier.Depot(kapital=10000)

    def test_gute_order_wird_erlaubt(self):
        self.assertTrue(wache.order_pruefen(self._depot(), "BTC",
                                            100.0, 98.0, 5.0))

    def test_ohne_stop_abgelehnt(self):
        p = wache.order_pruefen(self._depot(), "BTC", 100.0, None, 5.0)
        self.assertFalse(p)
        self.assertTrue(any("Stop-Loss" in g for g in p.gruende))

    def test_zu_grosse_position_abgelehnt(self):
        p = wache.order_pruefen(self._depot(), "BTC", 100.0, 98.0, 50.0)
        self.assertFalse(p)
        self.assertTrue(any("Einzelposition" in g for g in p.gruende))

    def test_positionsgrenze(self):
        d = self._depot()
        for i in range(konfig.POSITIONEN_MAX):
            d.kaufen("W%d" % i, 1.0, 100.0, 98.0, 106.0)
        p = wache.order_pruefen(d, "NEU", 100.0, 98.0, 1.0)
        self.assertFalse(p)
        self.assertTrue(any("Positionsgrenze" in g for g in p.gruende))

    def test_notbremse_blockiert_alles(self):
        wache.notbremse_ziehen("hand", "Test")
        p = wache.order_pruefen(self._depot(), "BTC", 100.0, 98.0, 5.0)
        self.assertFalse(p)
        self.assertTrue(any("Notbremse" in g for g in p.gruende))

    def test_notbremse_ueberlebt_neustart(self):
        wache.notbremse_ziehen("api", "Test")
        self.assertIsNotNone(wache.notbremse_stand())   # von der Platte
        self.assertTrue(wache.notbremse_loesen())
        self.assertIsNone(wache.notbremse_stand())

    def test_fehlerserie_zieht_notbremse(self):
        for _ in range(wache.API_FEHLER_GRENZE):
            wache.fehler_melden("api")
        self.assertIsNotNone(wache.notbremse_stand())

    def test_drawdown_grenze_zieht_notbremse(self):
        d = self._depot()
        d.hoechststand = 20000.0                  # Depot steht bei 10000
        p = wache.order_pruefen(d, "BTC", 100.0, 98.0, 1.0)
        self.assertFalse(p)
        self.assertTrue(any("Drawdown" in g for g in p.gruende))
        self.assertIsNotNone(wache.notbremse_stand())

    def test_tagesverlustgrenze(self):
        d = self._depot()
        d.tageswechsel()
        d.kapital_tagesbeginn = 12000.0           # heute schon 2000 verloren
        p = wache.order_pruefen(d, "BTC", 100.0, 98.0, 1.0)
        self.assertFalse(p)
        self.assertTrue(any("Tagesverlust" in g for g in p.gruende))


class LiveTorTest(unittest.TestCase):

    def test_live_ist_aus_vorgabe(self):
        self.assertFalse(konfig.LIVE_TRADING_ENABLED)

    def test_freigabe_wirft_immer(self):
        with self.assertRaises(tor.LiveGesperrt):
            tor.freigeben("BTC", bestaetigung_mensch=True)

    def test_zustand_nennt_offene_punkte(self):
        z = tor.live_zustand()
        self.assertFalse(z["aktiv"])
        self.assertTrue(z["fehlt"])

    def test_schalter_ist_streng(self):
        for wert in ("1", "yes", "True", "TRUE", " true"):
            os.environ["TEST_SCHALTER"] = wert
            self.assertFalse(konfig._schalter("TEST_SCHALTER"))
        os.environ["TEST_SCHALTER"] = "true"
        self.assertTrue(konfig._schalter("TEST_SCHALTER"))
        del os.environ["TEST_SCHALTER"]


class BacktestTest(unittest.TestCase):

    def test_zu_kurze_reihe_liefert_null_trades(self):
        e = motor.laufen(kerzen_bauen([100] * 20), vorlauf=60)
        self.assertEqual(e.bericht()["trades"], 0)

    def test_steigender_markt_wird_gehandelt(self):
        e = motor.laufen(kerzen_bauen(echter_aufwaertstrend()), kapital=10000)
        b = e.bericht()
        self.assertGreater(b["signale_trade"], 0)
        self.assertGreaterEqual(b["trades"], 1)

    def test_senkrechter_trend_wird_nicht_gekauft(self):
        """Eigenschaft des Modells, ausdruecklich festgehalten: ein Markt
        ohne jeden Ruecksetzer haelt den RSI bei 100 und gilt durchgehend
        als ueberkauft. Das System steigt dann nie ein - es verpasst
        Parabeln. Bewusst so: wer bei RSI 100 kauft, kauft die Spitze."""
        k = kerzen_bauen([100 * (1.004 ** i) for i in range(220)])
        self.assertEqual(motor.laufen(k, kapital=10000)
                         .bericht()["signale_trade"], 0)

    def test_fallender_markt_verliert_hoechstens_begrenzt(self):
        k = kerzen_bauen([200 * (0.995 ** i) for i in range(220)])
        e = motor.laufen(k, kapital=10000)
        # Mit Stop-Loss und 1 % Risiko je Trade darf ein durchgehend
        # fallender Markt das Depot nicht halbieren.
        self.assertGreater(e.bericht()["kapital_ende"], 7000)

    def test_kein_blick_in_die_zukunft(self):
        """Der entscheidende Test.

        Zwei Reihen sind bis Kerze 150 identisch und laufen danach
        auseinander - einmal steil hoch, einmal steil runter. Der
        Backtest darf bis Kerze 150 in beiden Faellen exakt gleich
        entscheiden. Tut er das nicht, hat er die Zukunft gelesen.
        """
        gemeinsam = [100 * (1.002 ** i) for i in range(151)]
        hoch = gemeinsam + [gemeinsam[-1] * (1.05 ** i) for i in range(1, 60)]
        runter = gemeinsam + [gemeinsam[-1] * (0.95 ** i) for i in range(1, 60)]

        e_hoch = motor.laufen(kerzen_bauen(hoch), kapital=10000)
        e_runter = motor.laufen(kerzen_bauen(runter), kapital=10000)

        bis = [(i, e) for i, e, _, _ in e_hoch.entscheide if i < 150]
        bis_r = [(i, e) for i, e, _, _ in e_runter.entscheide if i < 150]
        self.assertEqual(bis, bis_r)
        self.assertTrue(bis, "keine Entscheide zum Vergleichen")

    def test_gebuehren_werden_verrechnet(self):
        k = kerzen_bauen([100 * (1.004 ** i) for i in range(220)])
        e = motor.laufen(k, kapital=10000)
        if e.bericht()["trades"] > 0:
            self.assertGreater(e.bericht()["gebuehren_gesamt"], 0)

    def test_sharpe_ohne_daten_ist_none(self):
        e = motor.laufen(kerzen_bauen([100] * 20), vorlauf=60)
        self.assertIsNone(e.sharpe())

    def test_max_drawdown_zwischen_null_und_eins(self):
        k = kerzen_bauen([100 + 20 * ((i // 20) % 2) for i in range(220)])
        dd = motor.laufen(k, kapital=10000).max_drawdown()
        self.assertGreaterEqual(dd, 0.0)
        self.assertLessEqual(dd, 1.0)


class SicherheitTest(unittest.TestCase):
    """Befunde aus dem /cso-Audit, als Test festgenagelt."""

    def test_kennung_kann_den_api_pfad_nicht_umbiegen(self):
        """quote() laesst mit der Vorgabe safe='/' Schraegstriche durch.
        Eine Kennung wie 'a/../../x' haette damit den Pfad veraendert."""
        from krypto.daten import quelle
        gesehen = []

        def falle(pfad, art, frisch_erzwingen=False):
            gesehen.append(pfad)
            return [[1, 1.0, 1.0, 1.0, 1.0]], {"quelle": "test", "alter_s": 0}

        echt, quelle._holen = quelle._holen, falle
        try:
            quelle.kerzen("a/../../evil")
        finally:
            quelle._holen = echt
        self.assertEqual(gesehen[0].count("/"), 3)   # /coins/<id>/ohlc
        self.assertIn("a%2F..%2F..%2Fevil", gesehen[0])

    def test_waehrung_aus_der_umgebung_wird_kodiert(self):
        from krypto.daten import quelle
        gesehen = []

        def falle(pfad, art, frisch_erzwingen=False):
            gesehen.append(pfad)
            return [], {"quelle": "test", "alter_s": 0}

        echt, quelle._holen = quelle._holen, falle
        try:
            quelle.markt(anzahl=5, waehrung="usd&admin=1")
        finally:
            quelle._holen = echt
        self.assertNotIn("&admin=1", gesehen[0])

    def test_zugangsdaten_sind_gitignoriert(self):
        """Ein .env im Arbeitsverzeichnis darf nie versionierbar sein."""
        wurzel = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        pfad = os.path.join(wurzel, ".gitignore")
        if not os.path.exists(pfad):
            self.skipTest("kein .gitignore im Wurzelverzeichnis")
        text = open(pfad, encoding="utf-8").read()
        for muster in (".env", "*.pem", "*.key"):
            self.assertIn(muster, text, "%s fehlt in .gitignore" % muster)

    def test_es_gibt_nur_eine_netzwerkadresse(self):
        from krypto.daten import quelle
        self.assertTrue(quelle.BASIS.startswith("https://"))
        self.assertEqual(quelle.BASIS, "https://api.coingecko.com/api/v3")


class ProtokollTest(unittest.TestCase):

    def test_schluessel_werden_geschwaerzt(self):
        e = protokoll._schwaerzen({"api_key": "geheim", "kurs": 100})
        self.assertEqual(e["api_key"], "<GESCHWAERZT>")
        self.assertEqual(e["kurs"], 100)

    def test_passwort_in_verschachtelter_struktur(self):
        e = protokoll._schwaerzen({"a": {"password": "x", "b": [1, 2]}})
        self.assertEqual(e["a"]["password"], "<GESCHWAERZT>")

    def test_langer_zufallsstring_wird_geschwaerzt(self):
        e = protokoll._schwaerzen({"text": "Fehler bei " + "A" * 40})
        self.assertIn("<GESCHWAERZT:lang>", e["text"])

    def test_mailadresse_wird_geschwaerzt(self):
        e = protokoll._schwaerzen({"text": "Login als kunde@beispiel.ch"})
        self.assertIn("<GESCHWAERZT:mail>", e["text"])

    def test_unbekannte_spur_wird_abgelehnt(self):
        with self.assertRaises(ValueError):
            protokoll.schreiben("erfunden", "test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
