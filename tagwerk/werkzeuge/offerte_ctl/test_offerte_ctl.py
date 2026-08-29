# Tests fuer offerte_ctl.
#
# Laufen ohne LibreOffice - die PDF-Erzeugung wird uebersprungen, wenn
# das Backend fehlt. Alles andere ist reine Datenverarbeitung und muss
# ueberall gruen sein.
#
#   python3 -m unittest test_offerte_ctl

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import backend  # noqa: E402
import offerte_ctl  # noqa: E402
import vorlage  # noqa: E402


class VorlageTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.mkdtemp()
        self.vorlage = os.path.join(self.ordner, "v.odt")
        vorlage.vorlage_erzeugen(
            self.vorlage, ["Hallo {{name}}", "Betrag {{betrag}}"])

    def test_ist_gueltiges_zip(self):
        self.assertTrue(zipfile.is_zipfile(self.vorlage))

    def test_mimetype_ist_erster_und_unkomprimiert(self):
        # Sonst erkennen manche Programme die Datei nicht als ODT.
        with zipfile.ZipFile(self.vorlage) as z:
            erster = z.infolist()[0]
        self.assertEqual(erster.filename, "mimetype")
        self.assertEqual(erster.compress_type, zipfile.ZIP_STORED)

    def test_felder_finden(self):
        self.assertEqual(vorlage.felder_finden(self.vorlage),
                         ["betrag", "name"])

    def test_felder_mit_leerraum(self):
        v = os.path.join(self.ordner, "w.odt")
        vorlage.vorlage_erzeugen(v, ["{{ kunde }}"])
        self.assertEqual(vorlage.felder_finden(v), ["kunde"])

    def test_kaputte_datei(self):
        kaputt = os.path.join(self.ordner, "kaputt.odt")
        with open(kaputt, "w") as f:
            f.write("kein zip")
        with self.assertRaises(vorlage.VorlagenFehler):
            vorlage.felder_finden(kaputt)


class FuellenTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.mkdtemp()
        self.vorlage = os.path.join(self.ordner, "v.odt")
        vorlage.vorlage_erzeugen(
            self.vorlage, ["Hallo {{name}}", "Betrag {{betrag}}"])
        self.ziel = os.path.join(self.ordner, "z.odt")

    def _inhalt(self, pfad):
        with zipfile.ZipFile(pfad) as z:
            return z.read("content.xml").decode("utf-8")

    def test_ersetzt_werte(self):
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "Meier", "betrag": "100"})
        inhalt = self._inhalt(self.ziel)
        self.assertIn("Hallo Meier", inhalt)
        self.assertNotIn("{{name}}", inhalt)

    def test_sonderzeichen_werden_escaped(self):
        # Ein Kundenname wie "Meier & Co <AG>" wuerde die XML-Datei sonst
        # zerstoeren - die Offerte liesse sich nicht mehr oeffnen.
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "Meier & Co <AG>", "betrag": "1"})
        inhalt = self._inhalt(self.ziel)
        self.assertIn("Meier &amp; Co &lt;AG&gt;", inhalt)
        self.assertNotIn("Meier & Co", inhalt)

    def test_fehlender_wert_ist_streng_ein_fehler(self):
        # Wichtig: Eine Offerte mit "{{betrag}}" im Text geht an einen
        # Kunden und blamiert den Betrieb.
        with self.assertRaises(vorlage.VorlagenFehler):
            vorlage.fuellen(self.vorlage, self.ziel, {"name": "Meier"})

    def test_locker_laesst_platzhalter_stehen(self):
        e = vorlage.fuellen(self.vorlage, self.ziel, {"name": "Meier"},
                            streng=False)
        self.assertEqual(e["offen"], ["betrag"])
        self.assertIn("{{betrag}}", self._inhalt(self.ziel))

    def test_zeilenumbruch_wird_zu_odf_umbruch(self):
        # Der Fehler, den erst der Blick ins fertige PDF gezeigt hat: ein
        # rohes "\n" im XML ist fuer ODF nur Leerraum. Drei Positionen
        # standen dadurch in einer einzigen Zeile.
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "a\nb\nc", "betrag": "1"})
        inhalt = self._inhalt(self.ziel)
        self.assertEqual(inhalt.count("<text:line-break/>"), 2)
        self.assertNotIn("a\nb", inhalt)

    def test_tab_wird_zu_odf_tab(self):
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "links\trechts", "betrag": "1"})
        self.assertIn("<text:tab/>", self._inhalt(self.ziel))

    def test_umbruch_wird_nicht_doppelt_escaped(self):
        # Reihenfolge zaehlt: erst escapen, dann uebersetzen. Sonst
        # stuende "&lt;text:line-break/&gt;" im Dokument.
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "a\nb", "betrag": "1"})
        self.assertNotIn("&lt;text:line-break", self._inhalt(self.ziel))

    def test_ergebnis_bleibt_gueltiges_zip(self):
        vorlage.fuellen(self.vorlage, self.ziel,
                        {"name": "Meier", "betrag": "1"})
        self.assertTrue(zipfile.is_zipfile(self.ziel))
        with zipfile.ZipFile(self.ziel) as z:
            self.assertEqual(z.infolist()[0].filename, "mimetype")


class RechnungTest(unittest.TestCase):
    """Die Summen entscheiden, ob eine Offerte stimmt."""

    def _daten(self):
        return {"mwst_satz": 8.1, "positionen": [
            {"menge": "45", "einheit": "m2", "bezeichnung": "Grundieren",
             "preis": 810},
            {"menge": "45", "einheit": "m2", "bezeichnung": "Deckanstrich",
             "preis": 1350},
            {"menge": "1", "einheit": "Pausch.", "bezeichnung": "Reinigung",
             "preis": 280}]}

    def test_total_aus_positionen(self):
        w = offerte_ctl.werte_aufbereiten(self._daten())
        self.assertEqual(w["total"], "2440.00")

    def test_mwst_und_brutto(self):
        w = offerte_ctl.werte_aufbereiten(self._daten())
        self.assertEqual(w["mwst_betrag"], "197.64")
        self.assertEqual(w["total_brutto"], "2637.64")

    def test_total_wird_nicht_aus_der_datei_uebernommen(self):
        # Wer in der Eingabedatei ein falsches Total angibt, bekommt
        # trotzdem das gerechnete - sonst passen Zeilen und Summe nicht
        # zusammen, und das ist ein Streit mit dem Kunden.
        d = self._daten()
        d["total"] = "99999"
        self.assertEqual(offerte_ctl.werte_aufbereiten(d)["total"],
                         "2440.00")

    def test_ohne_positionen(self):
        w = offerte_ctl.werte_aufbereiten({"positionen": []})
        self.assertEqual(w["total"], "0.00")
        self.assertEqual(w["total_brutto"], "0.00")

    def test_mwst_satz_ohne_nachkommastellen(self):
        w = offerte_ctl.werte_aufbereiten(
            {"mwst_satz": 8.1, "positionen": []})
        self.assertEqual(w["mwst_satz"], "8.1")

    def test_positionen_werden_gerendert(self):
        w = offerte_ctl.werte_aufbereiten(self._daten())
        self.assertIn("Grundieren", w["positionen"])
        self.assertIn("810.00", w["positionen"])
        self.assertEqual(len(w["positionen"].splitlines()), 3)

    def test_positionen_haben_spalten(self):
        # Ohne Tabs stehen die Betraege nicht untereinander.
        w = offerte_ctl.werte_aufbereiten(self._daten())
        for zeile in w["positionen"].splitlines():
            self.assertEqual(zeile.count("\t"), 2)


class CliTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.mkdtemp()

    def test_vorlage_neu_und_felder(self):
        ziel = os.path.join(self.ordner, "v.odt")
        self.assertEqual(offerte_ctl.main(["vorlage-neu", ziel]), 0)
        self.assertTrue(os.path.exists(ziel))
        self.assertEqual(offerte_ctl.main(["felder", ziel]), 0)

    def test_pruefen_laeuft_immer(self):
        self.assertEqual(offerte_ctl.main(["pruefen"]), 0)

    def test_fehlende_datei_gibt_fehlercode(self):
        self.assertEqual(
            offerte_ctl.main(["felder", "/gibt/es/nicht.odt"]), 1)

    def test_erstellen_ohne_pdf(self):
        ziel = os.path.join(self.ordner, "v.odt")
        offerte_ctl.main(["vorlage-neu", ziel])
        daten = os.path.join(self.ordner, "d.json")
        with open(daten, "w", encoding="utf-8") as f:
            json.dump({"firma": "Muster GmbH", "firma_adresse": "Weg 1",
                       "kunde": "Meier", "kunde_adresse": "Gasse 2",
                       "nummer": "1", "ort": "Jona", "datum": "01.01.2026",
                       "einleitung": "Gerne.", "gueltig_bis": "01.02.2026",
                       "unterschrift": "M.", "mwst_satz": 8.1,
                       "positionen": [{"menge": "1", "einheit": "St",
                                       "bezeichnung": "Arbeit",
                                       "preis": 100}]}, f)
        code = offerte_ctl.main(["erstellen", ziel, daten, "--ausgabe",
                                 self.ordner, "--nur-odt"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(
            os.path.join(self.ordner, "offerte-1.odt")))


class BackendTest(unittest.TestCase):

    def test_verfuegbar_liefert_bool(self):
        self.assertIsInstance(backend.verfuegbar(), bool)

    def test_fehlende_quelle(self):
        if not backend.verfuegbar():
            self.skipTest("LibreOffice nicht installiert")
        with self.assertRaises(backend.BackendFehler):
            backend.nach_pdf("/gibt/es/nicht.odt", tempfile.mkdtemp())

    def test_pdf_erzeugen(self):
        if not backend.verfuegbar():
            self.skipTest("LibreOffice nicht installiert")
        ordner = tempfile.mkdtemp()
        quelle = os.path.join(ordner, "q.odt")
        vorlage.vorlage_erzeugen(quelle, ["Testinhalt"])
        pdf = backend.nach_pdf(quelle, ordner)
        self.assertTrue(os.path.exists(pdf))
        with open(pdf, "rb") as f:
            self.assertEqual(f.read(4), b"%PDF")


class EndeZuEndeTest(unittest.TestCase):
    """Prueft, was der Kunde sieht - nicht, was das Programm meldet.

    Der Umbruch-Fehler ist an keinem Rueckgabewert aufgefallen. Alle
    Werte waren im Dokument, das Dokument war gueltig, der Exit-Code
    war 0 - und trotzdem standen drei Positionen in einer Zeile. Nur
    der Text aus dem fertigen PDF zeigt so etwas.
    """

    def test_positionen_stehen_auf_eigenen_zeilen(self):
        if not backend.verfuegbar():
            self.skipTest("LibreOffice nicht installiert")
        if not shutil.which("pdftotext"):
            self.skipTest("pdftotext nicht installiert (poppler-utils)")

        ordner = tempfile.mkdtemp()
        v = os.path.join(ordner, "v.odt")
        offerte_ctl.main(["vorlage-neu", v])
        daten = os.path.join(ordner, "d.json")
        with open(daten, "w", encoding="utf-8") as f:
            json.dump({"firma": "F", "firma_adresse": "A", "kunde": "K",
                       "kunde_adresse": "A", "nummer": "9", "ort": "O",
                       "datum": "D", "einleitung": "E", "gueltig_bis": "G",
                       "unterschrift": "U", "mwst_satz": 8.1,
                       "positionen": [
                           {"menge": "1", "einheit": "St",
                            "bezeichnung": "Erste", "preis": 100},
                           {"menge": "2", "einheit": "St",
                            "bezeichnung": "Zweite", "preis": 200},
                           {"menge": "3", "einheit": "St",
                            "bezeichnung": "Dritte", "preis": 300}]}, f)
        self.assertEqual(
            offerte_ctl.main(["erstellen", v, daten, "--ausgabe", ordner]), 0)

        text = subprocess.run(
            ["pdftotext", "-layout", os.path.join(ordner, "offerte-9.pdf"),
             "-"], capture_output=True, text=True, timeout=60).stdout
        zeilen = [z for z in text.splitlines() if "Erste" in z or
                  "Zweite" in z or "Dritte" in z]
        self.assertEqual(len(zeilen), 3, "Positionen stehen nicht auf "
                         "eigenen Zeilen:\n%s" % text)
        self.assertIn("600.00", text)   # Total exkl.
        self.assertIn("48.60", text)    # MwSt 8.1%
        self.assertIn("648.60", text)   # Total inkl.


if __name__ == "__main__":
    unittest.main()
