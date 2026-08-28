# Tests der Eingangspruefung.
#
# Diese Schicht ist die Wand zum offenen Internet. Jeder Test hier steht
# fuer einen Angriff, der ohne ihn funktioniert.

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))

from webhook import (EingangFehler, Wiedereinspielsperre,  # noqa: E402
                     eingang_pruefen, mandant_zuordnen,
                     nummer_normalisieren, signatur_erzeugen,
                     signatur_pruefen)

SECRET = "geheim-app-secret"


class SignaturTest(unittest.TestCase):

    def test_gueltige_signatur(self):
        koerper = b'{"a": 1}'
        self.assertTrue(signatur_pruefen(
            koerper, signatur_erzeugen(koerper, SECRET), SECRET))

    def test_manipulierter_koerper_faellt_auf(self):
        koerper = b'{"stunden": 3}'
        kopf = signatur_erzeugen(koerper, SECRET)
        with self.assertRaises(EingangFehler):
            signatur_pruefen(b'{"stunden": 300}', kopf, SECRET)

    def test_falsches_secret(self):
        koerper = b'{"a": 1}'
        kopf = signatur_erzeugen(koerper, "anderes-secret")
        with self.assertRaises(EingangFehler):
            signatur_pruefen(koerper, kopf, SECRET)

    def test_fehlende_signatur(self):
        with self.assertRaises(EingangFehler):
            signatur_pruefen(b"{}", None, SECRET)
        with self.assertRaises(EingangFehler):
            signatur_pruefen(b"{}", "", SECRET)

    def test_falsches_praefix(self):
        with self.assertRaises(EingangFehler):
            signatur_pruefen(b"{}", "sha1=abc", SECRET)

    def test_fehlendes_secret_ist_startfehler_keine_freigabe(self):
        # Der Kernfehler aus javier-mobile: ohne Geheimnis wurde dort
        # jede Anfrage durchgelassen. Hier muss sie scheitern.
        koerper = b"{}"
        with self.assertRaises(EingangFehler):
            signatur_pruefen(koerper, signatur_erzeugen(koerper, SECRET), "")
        with self.assertRaises(EingangFehler):
            signatur_pruefen(koerper, "sha256=x", None)

    def test_text_statt_bytes_wird_abgewiesen(self):
        # Wer hier einen String hereingibt, hat vermutlich schon geparst
        # und wuerde gegen den falschen Inhalt pruefen.
        with self.assertRaises(EingangFehler):
            signatur_pruefen('{"a": 1}', "sha256=x", SECRET)

    def test_signatur_deckt_den_exakten_wortlaut_ab(self):
        # Zwei JSON-Dokumente mit gleichem Inhalt, aber anderem Leerraum,
        # haben verschiedene Signaturen. Genau deshalb der Rohkoerper.
        a = json.dumps({"x": 1}).encode()
        b = json.dumps({"x": 1}, indent=2).encode()
        with self.assertRaises(EingangFehler):
            signatur_pruefen(b, signatur_erzeugen(a, SECRET), SECRET)


class NummerTest(unittest.TestCase):

    def test_schreibweisen_vereinheitlicht(self):
        for eingabe in ("+41 79 123 45 67", "0041791234567",
                        "41791234567", "+41791234567"):
            self.assertEqual(nummer_normalisieren(eingabe), "+41791234567")

    def test_leer(self):
        self.assertEqual(nummer_normalisieren(""), "")
        self.assertEqual(nummer_normalisieren(None), "")
        self.assertEqual(nummer_normalisieren("abc"), "")


class ZuordnungTest(unittest.TestCase):

    def setUp(self):
        self.verzeichnis = {"+41791234567": "malerei-huber"}

    def test_bekannte_nummer(self):
        self.assertEqual(
            mandant_zuordnen("+41 79 123 45 67", self.verzeichnis),
            "malerei-huber")

    def test_unbekannte_nummer_wird_abgewiesen(self):
        # Kein Anlegen unterwegs.
        with self.assertRaises(EingangFehler):
            mandant_zuordnen("+41790000000", self.verzeichnis)

    def test_fehlende_nummer(self):
        with self.assertRaises(EingangFehler):
            mandant_zuordnen("", self.verzeichnis)


class WiedereinspielungTest(unittest.TestCase):

    def test_erste_nachricht_ist_neu(self):
        s = Wiedereinspielsperre()
        self.assertFalse(s.schon_gesehen("wamid.1"))

    def test_zweite_zustellung_wird_erkannt(self):
        s = Wiedereinspielsperre()
        s.vermerken("wamid.1")
        self.assertTrue(s.schon_gesehen("wamid.1"))

    def test_andere_id_bleibt_neu(self):
        s = Wiedereinspielsperre()
        s.vermerken("wamid.1")
        self.assertFalse(s.schon_gesehen("wamid.2"))

    def test_alte_eintraege_verfallen(self):
        uhr = {"t": 1000.0}
        s = Wiedereinspielsperre(fenster_sekunden=60,
                                 jetzt=lambda: uhr["t"])
        s.vermerken("wamid.1")
        self.assertTrue(s.schon_gesehen("wamid.1"))
        uhr["t"] += 61
        self.assertFalse(s.schon_gesehen("wamid.1"))
        self.assertEqual(len(s), 0)

    def test_id_ist_pflicht(self):
        s = Wiedereinspielsperre()
        with self.assertRaises(EingangFehler):
            s.schon_gesehen(None)
        with self.assertRaises(EingangFehler):
            s.vermerken("")


class GesamtpruefungTest(unittest.TestCase):

    def setUp(self):
        self.verzeichnis = {"+41791234567": "malerei-huber"}
        self.sperre = Wiedereinspielsperre()
        self.nutzlast = {"nachricht_id": "wamid.1",
                         "absender": "+41791234567",
                         "medien_id": "media-42"}
        self.koerper = json.dumps(self.nutzlast).encode()
        self.kopf = signatur_erzeugen(self.koerper, SECRET)

    def _pruefen(self):
        return eingang_pruefen(self.koerper, self.kopf, SECRET,
                               self.nutzlast, self.verzeichnis, self.sperre)

    def test_gueltiger_eingang(self):
        eingang = self._pruefen()
        self.assertEqual(eingang.mandant_id, "malerei-huber")
        self.assertEqual(eingang.medien_id, "media-42")
        self.assertEqual(eingang.absender, "+41791234567")

    def test_zweiter_versuch_wird_abgewiesen(self):
        self._pruefen()
        with self.assertRaises(EingangFehler):
            self._pruefen()

    def test_ungueltige_signatur_stoppt_vor_allem_anderen(self):
        self.kopf = "sha256=falsch"
        with self.assertRaises(EingangFehler):
            self._pruefen()
        # Entscheidend: Die Nachricht darf NICHT vermerkt worden sein,
        # sonst blockiert eine gefaelschte Anfrage die echte.
        self.assertEqual(len(self.sperre), 0)

    def test_fremde_nummer_wird_abgewiesen(self):
        self.nutzlast["absender"] = "+41790000000"
        self.koerper = json.dumps(self.nutzlast).encode()
        self.kopf = signatur_erzeugen(self.koerper, SECRET)
        with self.assertRaises(EingangFehler):
            self._pruefen()

    def test_nachricht_ohne_audio(self):
        self.nutzlast.pop("medien_id")
        self.koerper = json.dumps(self.nutzlast).encode()
        self.kopf = signatur_erzeugen(self.koerper, SECRET)
        with self.assertRaises(EingangFehler):
            self._pruefen()

    def test_abgewiesene_nachricht_blockiert_spaeteren_versuch_nicht(self):
        # Eine Nachricht ohne Audio darf nicht als "verarbeitet" gelten.
        self.nutzlast.pop("medien_id")
        koerper = json.dumps(self.nutzlast).encode()
        with self.assertRaises(EingangFehler):
            eingang_pruefen(koerper, signatur_erzeugen(koerper, SECRET),
                            SECRET, self.nutzlast, self.verzeichnis,
                            self.sperre)
        self.assertEqual(len(self.sperre), 0)


if __name__ == "__main__":
    unittest.main()
