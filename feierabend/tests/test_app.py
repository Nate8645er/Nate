# Tests des Webdienstes.
#
# Der wichtigste Test in dieser Datei ist die Mandantentrennung. Der
# klassische Bruch in einem Mehrmandanten-Dienst ist ein vergessener
# Filter - und er faellt niemandem auf, bis ein Betrieb die Rapporte
# eines anderen sieht.

import os
import sys
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "core"))
sys.path.insert(0, os.path.join(HIER, "..", "app"))

# Eigene Datenbankdatei je Testlauf, damit Tests nichts Echtes anfassen.
_temp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_temp.close()
os.environ["FEIERABEND_DB"] = _temp.name

import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


class Basis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.anlegen()
        cls.client = TestClient(app)
        db.betrieb_anlegen("maler", "Malerei Huber")
        db.betrieb_anlegen("elektro", "Elektro Winter")
        cls.code_a = db.mitarbeiter_anlegen("maler", "Nate")["code"]
        cls.code_b = db.mitarbeiter_anlegen("elektro", "Toni")["code"]
        db.kunde_anlegen("maler", "Meier")
        db.kunde_anlegen("elektro", "Bucher")

    @classmethod
    def tearDownClass(cls):
        os.unlink(_temp.name)

    def kopf(self, code):
        return {"X-Code": code}


class AnmeldungTest(Basis):

    def test_gueltiger_code(self):
        a = self.client.post("/api/anmelden", json={"code": self.code_a})
        self.assertEqual(a.status_code, 200)
        self.assertEqual(a.json()["betrieb"], "Malerei Huber")

    def test_unbekannter_code(self):
        a = self.client.post("/api/anmelden", json={"code": "XXXXXX"})
        self.assertEqual(a.status_code, 401)

    def test_leerer_code(self):
        a = self.client.post("/api/anmelden", json={"code": ""})
        self.assertEqual(a.status_code, 401)

    def test_code_ohne_kopfzeile_wird_abgewiesen(self):
        # Kein Zugangscode heisst kein Zugriff - nicht "dann halt offen".
        self.assertEqual(self.client.get("/api/kunden").status_code, 401)
        self.assertEqual(self.client.get("/api/rapporte").status_code, 401)
        self.assertEqual(self.client.get("/api/auswertung").status_code, 401)

    def test_kleinschreibung_wird_akzeptiert(self):
        a = self.client.post("/api/anmelden",
                             json={"code": self.code_a.lower()})
        self.assertEqual(a.status_code, 200)


class MandantentrennungTest(Basis):
    """Der Test, wegen dessen diese Datei existiert."""

    def test_kunden_bleiben_beim_eigenen_betrieb(self):
        a = self.client.get("/api/kunden", headers=self.kopf(self.code_a))
        b = self.client.get("/api/kunden", headers=self.kopf(self.code_b))
        namen_a = [k["name"] for k in a.json()["kunden"]]
        namen_b = [k["name"] for k in b.json()["kunden"]]
        self.assertIn("Meier", namen_a)
        self.assertNotIn("Meier", namen_b)
        self.assertIn("Bucher", namen_b)
        self.assertNotIn("Bucher", namen_a)

    def test_rapporte_bleiben_beim_eigenen_betrieb(self):
        self.client.post("/api/rapport", headers=self.kopf(self.code_a),
                         json={"datum": "2026-08-28", "kunde": "Meier",
                               "stunden": 3.0})
        eigene = self.client.get("/api/rapporte",
                                 headers=self.kopf(self.code_a)).json()
        fremde = self.client.get("/api/rapporte",
                                 headers=self.kopf(self.code_b)).json()
        self.assertTrue(any(r["kunde"] == "Meier" for r in eigene["rapporte"]))
        self.assertFalse(any(r["kunde"] == "Meier"
                             for r in fremde["rapporte"]))

    def test_auswertung_bleibt_beim_eigenen_betrieb(self):
        self.client.post("/api/rapport", headers=self.kopf(self.code_a),
                         json={"datum": "2026-08-28", "kunde": "Meier",
                               "stunden": 2.0})
        fremd = self.client.get("/api/auswertung",
                                headers=self.kopf(self.code_b)).json()
        self.assertEqual(fremd["je_kunde"], [])
        self.assertEqual(fremd["stunden_total"], 0)


class RapportTest(Basis):

    def test_speichern(self):
        a = self.client.post("/api/rapport", headers=self.kopf(self.code_a),
                             json={"datum": "2026-08-28", "kunde": "Meier",
                                   "stunden": 3.5,
                                   "taetigkeiten": "Wand grundiert",
                                   "material": ["Grundierung"]})
        self.assertEqual(a.status_code, 200)
        self.assertTrue(a.json()["gespeichert"])

    def test_ohne_kunde_abgelehnt(self):
        a = self.client.post("/api/rapport", headers=self.kopf(self.code_a),
                             json={"datum": "2026-08-28", "kunde": "  ",
                                   "stunden": 3.0})
        self.assertEqual(a.status_code, 400)

    def test_unplausible_stunden_abgelehnt(self):
        for stunden in (26, 0.1, -3):
            a = self.client.post(
                "/api/rapport", headers=self.kopf(self.code_a),
                json={"datum": "2026-08-28", "kunde": "Meier",
                      "stunden": stunden})
            self.assertEqual(a.status_code, 400, "Stunden %s" % stunden)

    def test_auswertung_gruppiert_nach_kunde_nicht_mitarbeiter(self):
        # Bewusste Entscheidung wegen Art. 328b OR: keine personenbezogene
        # Rangliste. Die Auswertung darf keine Mitarbeiternamen tragen.
        a = self.client.get("/api/auswertung",
                            headers=self.kopf(self.code_a)).json()
        self.assertIn("je_kunde", a)
        self.assertNotIn("je_mitarbeiter", a)
        for zeile in a["je_kunde"]:
            self.assertNotIn("mitarbeiter", zeile)


class EntwurfTest(Basis):

    def test_leerer_text(self):
        a = self.client.post("/api/entwurf", headers=self.kopf(self.code_a),
                             json={"text": "   "})
        self.assertEqual(a.status_code, 400)

    def test_ohne_schluessel_sauberer_fehler(self):
        # Ohne ANTHROPIC_API_KEY muss der Dienst ehrlich 503 melden statt
        # zu raten oder leer zu speichern.
        alt = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            a = self.client.post("/api/entwurf",
                                 headers=self.kopf(self.code_a),
                                 json={"text": "Fertig bei Meier"})
            self.assertEqual(a.status_code, 503)
            self.assertIn("ANTHROPIC_API_KEY", a.json()["fehler"])
        finally:
            if alt:
                os.environ["ANTHROPIC_API_KEY"] = alt


class StatusTest(Basis):

    def test_status_ohne_anmeldung(self):
        a = self.client.get("/api/status")
        self.assertEqual(a.status_code, 200)
        self.assertTrue(a.json()["bereit"])


if __name__ == "__main__":
    unittest.main()
