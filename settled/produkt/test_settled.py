# Tests fuer SETTLED.
#
# Der Abgleich wird ohne Netz getestet: die Kettendaten werden
# eingespeist. Ein Buchhaltungswerkzeug, das man nur mit Live-Ketten
# testen kann, ist nicht testbar - und dann glaubt man ihm irgendwann
# Zahlen, die nie geprueft wurden.
#
#   python3 -m unittest test_settled

import os
import sys
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import abgleich          # noqa: E402
import ketten            # noqa: E402
import settled           # noqa: E402

TAG = 86400
T0 = 1756000000          # fester Bezugspunkt, damit Tests reproduzierbar sind


def bestellung(nummer, betrag, zeit=T0, waehrung="USDT-TRC20"):
    return abgleich.Bestellung(nummer, betrag, waehrung, zeit)


def eingang(betrag, zeit=T0, waehrung="USDT-TRC20", tx=None):
    return ketten.Eingang("tron", waehrung, betrag, zeit,
                          tx or "tx%s" % betrag)


class ZeitTest(unittest.TestCase):

    def test_formate(self):
        for wert in ("2026-08-24", "24.08.2026", "2026-08-24 00:00:00",
                     "2026-08-24T00:00:00Z"):
            self.assertEqual(abgleich.zeit_lesen(wert), 1787529600, wert)

    def test_unix_durchgereicht(self):
        self.assertEqual(abgleich.zeit_lesen("1756000000"), 1756000000)

    def test_unlesbar(self):
        with self.assertRaises(ValueError):
            abgleich.zeit_lesen("naechsten Dienstag")


class ZuordnungTest(unittest.TestCase):

    def test_glatte_zahlung(self):
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(100, T0 + 3600)])
        self.assertEqual(z[0]["status"], abgleich.BEZAHLT)

    def test_unterbezahlt(self):
        # Der haeufigste reale Fall: der Absender zieht die Gebuehr ab.
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(97.5, T0 + 3600)])
        self.assertEqual(z[0]["status"], abgleich.UNTERBEZAHLT)
        self.assertAlmostEqual(z[0]["differenz"], -2.5)

    def test_ueberbezahlt(self):
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(105, T0 + 3600)])
        self.assertEqual(z[0]["status"], abgleich.UEBERBEZAHLT)

    def test_toleranz_bei_stablecoin(self):
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(99.5, T0 + 60)])
        self.assertEqual(z[0]["status"], abgleich.BEZAHLT)

    def test_offen_ohne_zahlung(self):
        z = abgleich.zuordnen([bestellung("1", 100)], [])
        self.assertEqual(z[0]["status"], abgleich.OFFEN)
        self.assertAlmostEqual(z[0]["differenz"], -100)

    def test_unerwarteter_eingang(self):
        z = abgleich.zuordnen([], [eingang(42)])
        self.assertEqual(z[0]["status"], abgleich.UNERWARTET)

    def test_eine_zahlung_begleicht_nur_eine_bestellung(self):
        # Ohne diese Regel liefert der Haendler zweimal.
        z = abgleich.zuordnen(
            [bestellung("1", 100), bestellung("2", 100)],
            [eingang(100, T0 + 3600)])
        self.assertEqual(sorted(x["status"] for x in z),
                         [abgleich.BEZAHLT, abgleich.OFFEN])

    def test_bestes_paar_gewinnt(self):
        # Die exakte Zahlung muss an die passende Bestellung gehen,
        # nicht an die zufaellig zuerst gepruefte.
        z = abgleich.zuordnen(
            [bestellung("klein", 50), bestellung("gross", 500)],
            [eingang(500, T0 + 100, tx="a"), eingang(50, T0 + 200, tx="b")])
        nach_nummer = {x["bestellung"].nummer: x for x in z
                       if x["bestellung"]}
        self.assertEqual(nach_nummer["klein"]["eingang"].tx, "b")
        self.assertEqual(nach_nummer["gross"]["eingang"].tx, "a")
        self.assertTrue(all(x["status"] == abgleich.BEZAHLT for x in z))

    def test_zahlung_vor_der_bestellung_zaehlt_nicht(self):
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(100, T0 - 10 * TAG)])
        self.assertEqual({x["status"] for x in z},
                         {abgleich.OFFEN, abgleich.UNERWARTET})

    def test_zahlung_lange_danach_zaehlt_nicht(self):
        z = abgleich.zuordnen([bestellung("1", 100)],
                              [eingang(100, T0 + 30 * TAG)])
        self.assertEqual({x["status"] for x in z},
                         {abgleich.OFFEN, abgleich.UNERWARTET})

    def test_fremde_waehrung_zaehlt_nicht(self):
        z = abgleich.zuordnen([bestellung("1", 100, waehrung="USDT")],
                              [eingang(100, T0 + 60, waehrung="BTC")])
        self.assertEqual({x["status"] for x in z},
                         {abgleich.OFFEN, abgleich.UNERWARTET})


class BewertungTest(unittest.TestCase):

    def test_fiatwert_am_eingangstag(self):
        z = abgleich.zuordnen([bestellung("1", 100)], [eingang(100, T0 + 60)])
        abgleich.bewerten(z, lambda w, t, f: 0.81, "chf")
        self.assertEqual(z[0]["fiat"], 81.0)

    def test_kursfehler_bricht_nicht_ab(self):
        def kaputt(w, t, f):
            raise RuntimeError("CoinGecko am Limit")
        z = abgleich.zuordnen([bestellung("1", 100)], [eingang(100, T0 + 60)])
        abgleich.bewerten(z, kaputt, "chf")
        self.assertIsNone(z[0]["fiat"])
        self.assertIn("CoinGecko", z[0]["kurs_fehler"])

    def test_unbewertete_werden_gezaehlt(self):
        def kaputt(w, t, f):
            raise RuntimeError("x")
        z = abgleich.zuordnen([bestellung("1", 100)], [eingang(100, T0 + 60)])
        abgleich.bewerten(z, kaputt, "chf")
        self.assertEqual(abgleich.zusammenfassen(z)["unbewertet"], 1)

    def test_zusammenfassung_zaehlt_fehlbetrag(self):
        z = abgleich.zuordnen(
            [bestellung("1", 100), bestellung("2", 50)],
            [eingang(90, T0 + 60)])
        s = abgleich.zusammenfassen(z)
        self.assertEqual(s[abgleich.UNTERBEZAHLT], 1)
        self.assertEqual(s[abgleich.OFFEN], 1)
        self.assertAlmostEqual(s["fehlbetrag"], -60.0)


class CsvTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.mkdtemp()

    def _schreiben(self, inhalt):
        pfad = os.path.join(self.ordner, "b.csv")
        with open(pfad, "w", encoding="utf-8") as f:
            f.write(inhalt)
        return pfad

    def test_semikolon(self):
        p = self._schreiben(
            "bestellnummer;betrag;waehrung;datum\n"
            "1001;100.50;USDT-TRC20;2026-08-24\n")
        b = abgleich.bestellungen_lesen(p)
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0].nummer, "1001")
        self.assertAlmostEqual(b[0].betrag, 100.50)

    def test_komma_als_trenner(self):
        p = self._schreiben(
            "bestellnummer,betrag,waehrung,datum\n"
            "1002,50,USDT,2026-08-24\n")
        self.assertEqual(len(abgleich.bestellungen_lesen(p)), 1)

    def test_schweizer_zahlenformat(self):
        p = self._schreiben(
            "bestellnummer;betrag;waehrung;datum\n"
            "1003;1'250.75;USDT;2026-08-24\n")
        self.assertAlmostEqual(abgleich.bestellungen_lesen(p)[0].betrag,
                               1250.75)

    def test_zeile_ohne_betrag_wird_uebersprungen(self):
        p = self._schreiben(
            "bestellnummer;betrag;waehrung;datum\n"
            "1004;;USDT;2026-08-24\n1005;10;USDT;2026-08-24\n")
        self.assertEqual(len(abgleich.bestellungen_lesen(p)), 1)


class KettenTest(unittest.TestCase):

    def test_unbekannte_waehrung(self):
        with self.assertRaises(ketten.KettenFehler):
            ketten.eingaenge_lesen("egal", "DOGE")

    def test_adresse_als_topic(self):
        t = ketten._adresse_als_topic(
            "0x28C6c06298d514Db089934071355E5743bf21d60")
        self.assertEqual(len(t), 66)
        self.assertTrue(t.endswith("28c6c06298d514db089934071355e5743bf21d60"))

    def test_token_tabelle_vollstaendig(self):
        for name, t in ketten.TOKEN.items():
            self.assertIn("kette", t, name)
            self.assertIn("dezimalen", t, name)
            self.assertIn("coingecko", t, name)


class CliTest(unittest.TestCase):

    def test_ketten_befehl(self):
        self.assertEqual(settled.main(["ketten", "--json"]), 0)

    def test_fehlende_datei(self):
        self.assertEqual(settled.main(
            ["abgleich", "--bestellungen", "/gibt/es/nicht.csv",
             "--adresse", "x", "--waehrung", "USDT"]), 1)


if __name__ == "__main__":
    unittest.main()
