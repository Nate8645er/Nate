# Tests der Pseudonymisierung.
#
# Diese Schicht entscheidet, ob Kundennamen die eigene Infrastruktur
# verlassen. Faellt sie still aus, fliessen Namen und Adressen von
# Menschen an ein Sprachmodell, die davon nichts wissen. Entsprechend
# gruendlich getestet.

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from pseudonym import (Kunde, Pseudonymisierer,  # noqa: E402
                       normalisieren)


def _stamm():
    return [
        Kunde(id=7, name="Meier"),
        Kunde(id=12, name="Müller-Schmid"),
        Kunde(id=3, name="Familie Zimmermann", aliase=["Zimmi"]),
        Kunde(id=21, name="Bäckerei Huber"),
    ]


class NormalisierenTest(unittest.TestCase):

    def test_umlaute(self):
        self.assertEqual(normalisieren("Müller"), "mueller")
        self.assertEqual(normalisieren("Bäckerei"), "baeckerei")

    def test_anrede_faellt_weg(self):
        self.assertEqual(normalisieren("Familie Meier"), "meier")
        self.assertEqual(normalisieren("Herr Meier"), "meier")
        self.assertEqual(normalisieren("Frau Müller"), "mueller")

    def test_satzzeichen_weg(self):
        self.assertEqual(normalisieren("Meier,"), "meier")

    def test_leer(self):
        self.assertEqual(normalisieren(""), "")
        self.assertEqual(normalisieren(None), "")


class ErsetzenTest(unittest.TestCase):

    def setUp(self):
        self.p = Pseudonymisierer(_stamm())

    def test_einfacher_name(self):
        z = self.p.pseudonymisieren("Fertig bei Meier, drei Stunden.")
        self.assertIn("KUNDE_7", z.text)
        self.assertNotIn("Meier", z.text)

    def test_mit_anrede(self):
        z = self.p.pseudonymisieren("Bei Familie Meier war ich drei Stunden.")
        self.assertIn("KUNDE_7", z.text)
        self.assertNotIn("Meier", z.text)

    def test_umlaut_variante_wird_erkannt(self):
        # Transkription schreibt "Mueller-Schmid" statt "Müller-Schmid".
        z = self.p.pseudonymisieren("Zwei Stunden bei Mueller-Schmid.")
        self.assertIn("KUNDE_12", z.text)

    def test_alias(self):
        z = self.p.pseudonymisieren("Kurz bei Zimmi vorbei.")
        self.assertIn("KUNDE_3", z.text)

    def test_laengerer_name_gewinnt(self):
        # "Müller-Schmid" darf nicht als "Müller" halb ersetzt werden,
        # und schon gar nicht dem falschen Kunden zugeordnet.
        z = self.p.pseudonymisieren("Bei Müller-Schmid gearbeitet.")
        self.assertIn("KUNDE_12", z.text)
        self.assertNotIn("Schmid", z.text)

    def test_mehrere_kunden(self):
        z = self.p.pseudonymisieren(
            "Morgens bei Meier, nachmittags bei Zimmi.")
        self.assertIn("KUNDE_7", z.text)
        self.assertIn("KUNDE_3", z.text)
        self.assertEqual(len(z.treffer), 2)
        self.assertFalse(z.eindeutig)

    def test_originalwortlaut_wird_gemerkt(self):
        z = self.p.pseudonymisieren("Bei Familie Meier gewesen.")
        self.assertIn("KUNDE_7", z.treffer)
        self.assertIn("Meier", z.treffer["KUNDE_7"])

    def test_unbekannter_kunde_bleibt_stehen(self):
        # Wichtig: nicht raten. Ein unbekannter Name muss als solcher
        # sichtbar bleiben, damit das System nachfragt.
        z = self.p.pseudonymisieren("Bei Familie Brunner gearbeitet.")
        self.assertIn("Brunner", z.text)
        self.assertIn("Brunner", z.unbekannt)

    def test_kein_falscher_treffer_bei_kurzen_namen(self):
        p = Pseudonymisierer([Kunde(id=1, name="Ott")])
        z = p.pseudonymisieren("Bei Ost gewesen.")
        self.assertNotIn("KUNDE_1", z.text)

    def test_leeres_transkript(self):
        z = self.p.pseudonymisieren("")
        self.assertEqual(z.text, "")
        self.assertEqual(z.treffer, {})

    def test_ohne_kunden_im_text(self):
        z = self.p.pseudonymisieren("Drei Stunden Wand gestrichen.")
        self.assertEqual(z.treffer, {})
        self.assertEqual(z.text, "Drei Stunden Wand gestrichen.")


class AufloesenTest(unittest.TestCase):

    def setUp(self):
        self.p = Pseudonymisierer(_stamm())

    def test_token_wird_zurueckgesetzt(self):
        self.assertEqual(self.p.aufloesen("Rapport fuer KUNDE_7"),
                         "Rapport fuer Meier")

    def test_mehrere_token(self):
        text = self.p.aufloesen("KUNDE_7 und KUNDE_3")
        self.assertIn("Meier", text)
        self.assertIn("Zimmermann", text)

    def test_unbekanntes_token_bleibt(self):
        self.assertEqual(self.p.aufloesen("KUNDE_999"), "KUNDE_999")

    def test_hin_und_zurueck(self):
        original = "Fertig bei Familie Meier, drei Stunden."
        z = self.p.pseudonymisieren(original)
        zurueck = self.p.aufloesen(z.text)
        self.assertIn("Meier", zurueck)
        self.assertNotIn("KUNDE_", zurueck)


class SicherheitsnetzTest(unittest.TestCase):
    """Die Pruefung, die vor jedem Modellaufruf laeuft."""

    def setUp(self):
        self.p = Pseudonymisierer(_stamm())

    def test_erkennt_verbliebenen_klarnamen(self):
        self.assertTrue(self.p.enthaelt_klarnamen("Bei Meier gewesen."))

    def test_pseudonymisierter_text_ist_sauber(self):
        z = self.p.pseudonymisieren("Fertig bei Familie Meier.")
        self.assertFalse(self.p.enthaelt_klarnamen(z.text))

    def test_text_ohne_kunden_ist_sauber(self):
        self.assertFalse(self.p.enthaelt_klarnamen("Wand gestrichen."))

    def test_mehrfachkunde_vollstaendig_ersetzt(self):
        z = self.p.pseudonymisieren(
            "Erst Meier, dann Mueller-Schmid, dann Zimmi.")
        self.assertFalse(self.p.enthaelt_klarnamen(z.text))


if __name__ == "__main__":
    unittest.main()
