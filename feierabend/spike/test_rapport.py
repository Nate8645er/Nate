# Tests fuer die Bewertungslogik des Vorversuchs.
#
# Laeuft ohne API-Schluessel und ohne Netz: python3 -m unittest discover
#
# Diese Tests sichern die Messlatte selbst ab. Wenn die Bewertung falsch
# misst, ist das Ergebnis des ganzen Vorversuchs wertlos - und die
# Entscheidung, ob das Produkt gebaut wird, beruht auf einer kaputten Zahl.

import unittest

from rapport import (STUNDEN_TOLERANZ, Rapport, auswerten, bewerte,
                     kunde_stimmt, material_stimmt, stunden_stimmen,
                     text_stimmt)


class KundeTest(unittest.TestCase):

    def test_identisch(self):
        self.assertTrue(kunde_stimmt("Meier", "Meier"))

    def test_anrede_wird_ignoriert(self):
        # Der Handwerker sagt "Familie Meier", im Stamm steht "Meier".
        self.assertTrue(kunde_stimmt("Meier", "Familie Meier"))
        self.assertTrue(kunde_stimmt("Familie Meier", "Meier"))

    def test_ortszusatz_schadet_nicht(self):
        self.assertTrue(kunde_stimmt("Meier", "Familie Meier in Jona"))

    def test_umlaute_werden_normalisiert(self):
        self.assertTrue(kunde_stimmt("Müller", "Mueller"))
        self.assertTrue(kunde_stimmt("Schäfer", "Familie Schaefer"))

    def test_grosskleinschreibung_egal(self):
        self.assertTrue(kunde_stimmt("meier", "MEIER"))

    def test_falscher_kunde(self):
        self.assertFalse(kunde_stimmt("Meier", "Huber"))

    def test_leer_ist_kein_treffer(self):
        self.assertFalse(kunde_stimmt("Meier", ""))

    def test_beide_leer(self):
        self.assertTrue(kunde_stimmt("", ""))


class StundenTest(unittest.TestCase):

    def test_exakt(self):
        self.assertTrue(stunden_stimmen(3.0, 3.0))

    def test_innerhalb_der_toleranz(self):
        # Eine Viertelstunde Abweichung ist erlaubt.
        self.assertTrue(stunden_stimmen(3.0, 3.25))
        self.assertTrue(stunden_stimmen(3.0, 2.75))

    def test_ausserhalb_der_toleranz(self):
        self.assertFalse(stunden_stimmen(3.0, 3.5))
        self.assertFalse(stunden_stimmen(3.0, 2.0))

    def test_fehlende_stunden_sind_kein_treffer(self):
        self.assertFalse(stunden_stimmen(3.0, None))

    def test_beide_fehlen(self):
        self.assertTrue(stunden_stimmen(None, None))

    def test_toleranzgrenze_zaehlt_als_treffer(self):
        self.assertTrue(stunden_stimmen(3.0, 3.0 + STUNDEN_TOLERANZ))


class MaterialTest(unittest.TestCase):

    def test_vollstaendig(self):
        self.assertEqual(
            material_stimmt(["Grundierung", "Abdeckband"],
                            ["Abdeckband", "Grundierung"]),
            1.0)

    def test_reihenfolge_egal(self):
        self.assertEqual(material_stimmt(["A", "B"], ["B", "A"]), 1.0)

    def test_teiltreffer_zaehlt_anteilig(self):
        note = material_stimmt(["Grundierung", "Abdeckband", "Pinsel"],
                               ["Grundierung", "Abdeckband"])
        self.assertAlmostEqual(note, 2 / 3)

    def test_dialektform_wird_erkannt(self):
        # "Grundierig" steckt in "Grundierung" nicht - aber umgekehrt
        # findet der Teilstringvergleich "Grundierig" in "Grundierigsfarb".
        self.assertEqual(material_stimmt(["Grundierig"], ["Grundierigsfarb"]),
                         1.0)

    def test_nichts_erwartet_nichts_erkannt(self):
        self.assertEqual(material_stimmt([], []), 1.0)

    def test_nichts_erwartet_aber_erfunden(self):
        # Halluziniertes Material ist ein Fehler, kein Bonus.
        self.assertEqual(material_stimmt([], ["Grundierung"]), 0.0)

    def test_erwartet_aber_nichts_erkannt(self):
        self.assertEqual(material_stimmt(["Grundierung"], []), 0.0)


class TextTest(unittest.TestCase):

    def test_stichworte_vorhanden(self):
        self.assertEqual(text_stimmt("Wand gestrichen", "Wand gestrichen"),
                         1.0)

    def test_teilweise(self):
        note = text_stimmt("Wand grundiert gestrichen",
                           "Wand grundiert")
        self.assertAlmostEqual(note, 2 / 3)

    def test_nichts_erwartet(self):
        self.assertEqual(text_stimmt("", "irgendwas"), 1.0)


class BewertungTest(unittest.TestCase):

    def _erwartet(self):
        return Rapport(kunde="Meier", stunden=3.0,
                       taetigkeiten="Wand grundiert",
                       material=["Grundierung", "Abdeckband"],
                       folgetermin="naechste Woche")

    def test_perfekter_rapport(self):
        ergebnis = bewerte(self._erwartet(), self._erwartet())
        self.assertEqual(ergebnis["gesamt"], 1.0)
        self.assertTrue(ergebnis["brauchbar"])

    def test_brauchbar_trotz_fehlendem_material(self):
        # Kunde und Stunden sitzen - der Rapport laesst sich verrechnen,
        # auch wenn das Material fehlt.
        schlecht = Rapport(kunde="Familie Meier", stunden=3.0)
        ergebnis = bewerte(self._erwartet(), schlecht)
        self.assertTrue(ergebnis["brauchbar"])
        self.assertLess(ergebnis["gesamt"], 1.0)

    def test_unbrauchbar_ohne_stunden(self):
        ohne = Rapport(kunde="Meier", stunden=None,
                       material=["Grundierung", "Abdeckband"])
        ergebnis = bewerte(self._erwartet(), ohne)
        self.assertFalse(ergebnis["brauchbar"])

    def test_unbrauchbar_bei_falschem_kunden(self):
        # Der gefaehrlichste Fall: alles stimmt, nur der Kunde ist falsch.
        # Dieser Rapport wuerde dem falschen Auftrag belastet.
        falsch = Rapport(kunde="Huber", stunden=3.0,
                         taetigkeiten="Wand grundiert",
                         material=["Grundierung", "Abdeckband"],
                         folgetermin="naechste Woche")
        ergebnis = bewerte(self._erwartet(), falsch)
        self.assertFalse(ergebnis["brauchbar"])


class RueckfrageTest(unittest.TestCase):

    def test_vollstaendiger_rapport_braucht_keine_rueckfrage(self):
        self.assertFalse(Rapport(kunde="Meier", stunden=3.0)
                         .braucht_rueckfrage())

    def test_fehlende_stunden_loesen_rueckfrage_aus(self):
        r = Rapport(kunde="Meier")
        self.assertTrue(r.braucht_rueckfrage())
        self.assertIn("stunden", r.fehlende_pflichtfelder())

    def test_leerer_kunde_loest_rueckfrage_aus(self):
        r = Rapport(kunde="   ", stunden=3.0)
        self.assertTrue(r.braucht_rueckfrage())
        self.assertIn("kunde", r.fehlende_pflichtfelder())


class AuswertungTest(unittest.TestCase):

    def _ergebnisse(self, brauchbar, gesamt):
        return [{"brauchbar": True, "gesamt": 1.0} for _ in range(brauchbar)] \
            + [{"brauchbar": False, "gesamt": 0.3}
               for _ in range(gesamt - brauchbar)]

    def test_bestanden_ab_schwelle(self):
        # 14 von 20 sind 70 Prozent - genau die Schwelle.
        ergebnis = auswerten(self._ergebnisse(14, 20))
        self.assertTrue(ergebnis["bestanden"])
        self.assertEqual(ergebnis["quote"], 0.7)

    def test_knapp_darunter_faellt_durch(self):
        ergebnis = auswerten(self._ergebnisse(13, 20))
        self.assertFalse(ergebnis["bestanden"])
        self.assertIn("Durchgefallen", ergebnis["urteil"])

    def test_ohne_testfaelle_kein_urteil(self):
        ergebnis = auswerten([])
        self.assertFalse(ergebnis["bestanden"])
        self.assertEqual(ergebnis["anzahl"], 0)


if __name__ == "__main__":
    unittest.main()
