# Tests des vollstaendigen Durchlaufs.
#
# Hier wird die Reihenfolge geprueft, auf der die Datenschutzarchitektur
# beruht - besonders, dass kein Klarname am Modell vorbeikommt.

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from pipeline import (Ergebnis, KlarnameEntwichen,  # noqa: E402
                      PipelineFehler, verarbeiten)
from pseudonym import Kunde  # noqa: E402
from webhook import Eingang  # noqa: E402

STAMM = [Kunde(id=7, name="Meier"),
         Kunde(id=12, name="Müller-Schmid"),
         Kunde(id=3, name="Bäckerei Huber")]

EINGANG = Eingang(mandant_id="malerei-huber", absender="+41791234567",
                  nachricht_id="wamid.1", medien_id="media-42")


def transkript(text):
    return lambda audio: text


def modell_mit(**felder):
    text = json.dumps(felder, ensure_ascii=False)
    return lambda anweisung, t: text


class DurchlaufTest(unittest.TestCase):

    def test_vollstaendiger_rapport(self):
        e = verarbeiten(
            EINGANG, b"audio", STAMM,
            transkript("Fertig bei Familie Meier, drei Stunden."),
            modell_mit(kunde_token="KUNDE_7", stunden=3,
                       taetigkeiten="Wand grundiert",
                       material=["Grundierung"]))
        self.assertEqual(e.kunde, "Meier")
        self.assertEqual(e.stunden, 3.0)
        self.assertTrue(e.vollstaendig)
        self.assertEqual(e.rueckfrage(), "")

    def test_mandant_wird_durchgereicht(self):
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Bei Meier gewesen."),
                        modell_mit(kunde_token="KUNDE_7", stunden=2))
        self.assertEqual(e.mandant_id, "malerei-huber")

    def test_leeres_transkript_bricht_ab(self):
        with self.assertRaises(PipelineFehler):
            verarbeiten(EINGANG, b"audio", STAMM, transkript(""),
                        modell_mit(stunden=3))

    def test_unbrauchbare_modellantwort_bricht_ab(self):
        with self.assertRaises(PipelineFehler):
            verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Bei Meier gewesen."),
                        lambda a, t: "Das kann ich nicht.")


class DatenschutzTest(unittest.TestCase):
    """Die Pruefungen, wegen derer diese Architektur so gebaut ist."""

    def test_modell_sieht_nur_das_token(self):
        gesehen = {}

        def modell(anweisung, text):
            gesehen["text"] = text
            return json.dumps({"kunde_token": "KUNDE_7", "stunden": 3})

        verarbeiten(EINGANG, b"audio", STAMM,
                    transkript("Fertig bei Familie Meier in Jona."), modell)
        self.assertIn("KUNDE_7", gesehen["text"])
        self.assertNotIn("Meier", gesehen["text"])

    def test_abbruch_wenn_klarname_stehen_bleibt(self):
        # Ein Pseudonymisierer, der versagt, darf den Durchlauf nicht
        # fortsetzen. Simuliert ueber einen Kunden, dessen Name im Text
        # in einer Form steht, die ersetzt werden muesste.
        class KaputterStamm(list):
            pass

        # Wir pruefen das Netz direkt: Text mit Klarnamen, aber leerer
        # Stamm - dann greift die Ersetzung nicht, das Netz aber auch
        # nicht, weil der Name unbekannt ist. Also mit Stamm, und wir
        # bauen den Fall ueber ein Transkript, das den Namen doppelt
        # nennt - einmal erkannt, einmal in anderer Schreibweise.
        stamm = [Kunde(id=7, name="Meier")]
        with self.assertRaises(KlarnameEntwichen):
            verarbeiten(EINGANG, b"audio", stamm,
                        transkript("Meier und nochmals Meier und Meier."),
                        modell_mit(stunden=3))

    def test_token_wird_im_freitext_zurueckgesetzt(self):
        e = verarbeiten(
            EINGANG, b"audio", STAMM,
            transkript("Bei Meier gewesen."),
            modell_mit(kunde_token="KUNDE_7", stunden=3,
                       taetigkeiten="Bei KUNDE_7 die Wand grundiert"))
        self.assertIn("Meier", e.taetigkeiten)
        self.assertNotIn("KUNDE_", e.taetigkeiten)


class RueckfrageTest(unittest.TestCase):

    def test_fehlende_stunden(self):
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Bei Meier gewesen."),
                        modell_mit(kunde_token="KUNDE_7"))
        self.assertFalse(e.vollstaendig)
        self.assertIn("Wie lange", e.rueckfrage())
        self.assertIn("Meier", e.rueckfrage())

    def test_fehlender_kunde(self):
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Drei Stunden gearbeitet."),
                        modell_mit(stunden=3))
        self.assertFalse(e.vollstaendig)
        self.assertIn("Kunden", e.rueckfrage())

    def test_beides_fehlt(self):
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Wand gestrichen."), modell_mit())
        self.assertIn("Kunden", e.rueckfrage())
        self.assertIn("wie lange", e.rueckfrage())

    def test_unbekannter_name_wird_erfragt(self):
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Bei Familie Brunner, drei Stunden."),
                        modell_mit(stunden=3))
        self.assertIn("Brunner", e.rueckfrage())
        self.assertIn("Brunner", e.unbekannte_namen)

    def test_unplausible_stunden_loesen_rueckfrage_aus(self):
        # Das Modell liefert 26 Stunden, die Extraktion verwirft sie -
        # daraus muss eine Rueckfrage werden, keine Speicherung.
        e = verarbeiten(EINGANG, b"audio", STAMM,
                        transkript("Bei Meier gewesen, den ganzen Tag."),
                        modell_mit(kunde_token="KUNDE_7", stunden=26))
        self.assertIsNone(e.stunden)
        self.assertIn("Wie lange", e.rueckfrage())


class ErgebnisTest(unittest.TestCase):

    def test_leerer_kunde_gilt_als_fehlend(self):
        e = Ergebnis(mandant_id="x", kunde="   ", stunden=3.0)
        self.assertIn("kunde", e.fehlende_pflichtfelder())

    def test_vollstaendig(self):
        e = Ergebnis(mandant_id="x", kunde="Meier", stunden=3.0)
        self.assertTrue(e.vollstaendig)


if __name__ == "__main__":
    unittest.main()
