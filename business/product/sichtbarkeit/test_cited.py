# Tests fuer CITED.
#
# Laufen ohne Netz: technik.pruefen bekommt eine eingespeiste Holfunktion.
# Ein Audit-Werkzeug, das man nur mit fremden Servern testen kann, ist
# nicht testbar - und dann glaubt man ihm irgendwann Zahlen, die es nie
# geprueft hat.
#
#   python3 -m unittest test_cited

import json
import os
import sys
import tempfile
import unittest

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

import bericht          # noqa: E402
import cited            # noqa: E402
import fragen           # noqa: E402
import netz             # noqa: E402
import technik          # noqa: E402


SEITE = """<!doctype html><html lang="de"><head>
<title>Meier Treuhand AG - Buchhaltung in Rapperswil</title>
<meta name="description" content="Treuhand fuer KMU.">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"LocalBusiness",
 "name":"Meier Treuhand AG","telephone":"+41 55 000 00 00"}
</script>
</head><body>
<h1>Meier Treuhand AG</h1>
<h2>Was kostet eine Buchhaltung?</h2>
<p>%s</p>
<script>var unsichtbar = "dieser Text zaehlt nicht";</script>
</body></html>""" % ("Wort " * 400)


def falsches_netz(karte):
    """Baut eine Holfunktion aus {Pfadende: (Status, Text)}."""
    def holen(url, zeitlimit=None):
        for ende, (status, text) in karte.items():
            if url.endswith(ende):
                return netz.Antwort(url, status, text, {}, 0.1, url)
        return netz.Antwort(url, 404, "", {}, 0.1, url)
    return holen


class RobotsTest(unittest.TestCase):

    def test_sammelgruppe_sperrt_alles(self):
        g = technik.robots_lesen("User-agent: *\nDisallow: /")
        self.assertTrue(technik.gesperrt(g, "GPTBot"))
        self.assertTrue(technik.gesperrt(g, "PerplexityBot"))

    def test_eigene_gruppe_schlaegt_sammelgruppe(self):
        g = technik.robots_lesen(
            "User-agent: *\nDisallow: /\n\n"
            "User-agent: OAI-SearchBot\nDisallow:\n")
        self.assertTrue(technik.gesperrt(g, "ClaudeBot"))
        self.assertFalse(technik.gesperrt(g, "OAI-SearchBot"))

    def test_leeres_disallow_erlaubt(self):
        g = technik.robots_lesen("User-agent: *\nDisallow:")
        self.assertFalse(technik.gesperrt(g, "GPTBot"))

    def test_mehrere_agenten_teilen_regeln(self):
        g = technik.robots_lesen(
            "User-agent: GPTBot\nUser-agent: ClaudeBot\nDisallow: /\n")
        self.assertTrue(technik.gesperrt(g, "GPTBot"))
        self.assertTrue(technik.gesperrt(g, "ClaudeBot"))
        self.assertFalse(technik.gesperrt(g, "PerplexityBot"))

    def test_kommentare_und_leerzeilen(self):
        g = technik.robots_lesen(
            "# Kommentar\n\nUser-agent: *  # noch einer\nDisallow: /admin\n")
        self.assertTrue(technik.gesperrt(g, "GPTBot", "/admin/x"))
        self.assertFalse(technik.gesperrt(g, "GPTBot", "/"))

    def test_allow_schlaegt_kuerzeres_disallow(self):
        g = technik.robots_lesen(
            "User-agent: *\nDisallow: /\nAllow: /blog\n")
        self.assertFalse(technik.gesperrt(g, "GPTBot", "/blog/beitrag"))
        self.assertTrue(technik.gesperrt(g, "GPTBot", "/intern"))


class SicherheitTest(unittest.TestCase):
    """Funde aus dem Security-Review. Jeder Test hielt einen echten Fehler.

    Das Werkzeug ruft fremdbestimmte Adressen ab und verarbeitet
    fremdes HTML. Jeder dieser Faelle war vorhanden und ausnutzbar.
    """

    def test_interne_adressen_werden_nicht_abgerufen(self):
        # Sonst laesst sich ueber den "Kunden"-Eingabewert der
        # Cloud-Metadatendienst auslesen und landet im Bericht.
        for ziel in ("http://169.254.169.254/latest/meta-data/",
                     "http://127.0.0.1/", "http://10.0.0.5/",
                     "http://localhost:8080/"):
            a = netz.holen(ziel, zeitlimit=5)
            self.assertIsNotNone(a.fehler, ziel)
            self.assertIsNone(a.status, ziel)

    def test_fremde_schemata_werden_abgelehnt(self):
        for eingabe in ("file://localhost/etc/passwd", "ftp://example.com",
                        "gopher://example.com"):
            with self.assertRaises(ValueError, msg=eingabe):
                netz.domain_normalisieren(eingabe)

    def test_holen_lehnt_fremdes_schema_ab(self):
        a = netz.holen("file:///etc/hostname")
        self.assertIsNotNone(a.fehler)
        self.assertEqual(a.text, "")

    def test_gzip_wird_begrenzt_entpackt(self):
        # Eine Zip-Bombe darf Speicher kosten, aber nicht beliebig viel.
        import zlib
        bombe = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
        roh = bombe.compress(b"A" * (50 * 1024 * 1024)) + bombe.flush()
        heraus = netz._entpacken(roh, "gzip", grenze=1024)
        self.assertLessEqual(len(heraus), 1024 + 65536)

    def test_wildcard_schlaegt_gleichwertiges_allow_nicht(self):
        # Der teuerste Fehler: ein falscher "gesperrt"-Befund im
        # Bericht eines zahlenden Kunden.
        g = technik.robots_lesen(
            "User-agent: OAI-SearchBot\nDisallow: /*\nAllow: /\n")
        self.assertFalse(technik.gesperrt(g, "OAI-SearchBot", "/"))

    def test_tiefes_jsonld_stuerzt_nicht_ab(self):
        tief = "[" * 60000 + "]" * 60000
        typen, kaputt = technik.jsonld_typen([tief])
        self.assertEqual(typen, [])
        self.assertEqual(kaputt, 1)


class HtmlTest(unittest.TestCase):

    def setUp(self):
        self.leser = technik._Leser()
        self.leser.feed(SEITE)

    def test_titel(self):
        self.assertIn("Meier Treuhand", self.leser.titel)

    def test_skript_zaehlt_nicht_zum_text(self):
        self.assertNotIn("unsichtbar", self.leser.sichtbarer_text)
        self.assertNotIn("zaehlt nicht", self.leser.sichtbarer_text)

    def test_ueberschrift_in_frageform(self):
        self.assertTrue(any("?" in u for u in self.leser.h2))

    def test_jsonld_typ(self):
        typen, kaputt = technik.jsonld_typen(self.leser.jsonld_roh)
        self.assertIn("LocalBusiness", typen)
        self.assertEqual(kaputt, 0)

    def test_kaputtes_jsonld_wird_gezaehlt(self):
        typen, kaputt = technik.jsonld_typen(['{"@type": '])
        self.assertEqual(typen, [])
        self.assertEqual(kaputt, 1)

    def test_unterarten_zaehlen_als_organisation(self):
        # Ein falscher Mangel im Audit kostet mehr Vertrauen als ein
        # uebersehener. NZZ traegt NewsMediaOrganization - das ist eine.
        for typ in ("NewsMediaOrganization", "Dentist", "LocalBusiness",
                    "AccountingService", "HomeAndConstructionBusiness"):
            self.assertTrue(technik._ist_organisation(typ), typ)

    def test_nicht_jeder_typ_ist_eine_organisation(self):
        for typ in ("WebSite", "BreadcrumbList", "Article", "Person"):
            self.assertFalse(technik._ist_organisation(typ), typ)

    def test_graph_wird_abgeflacht(self):
        typen, _ = technik.jsonld_typen(
            ['{"@graph":[{"@type":"Organization"},{"@type":"FAQPage"}]}'])
        self.assertEqual(typen, ["FAQPage", "Organization"])


class PruefungTest(unittest.TestCase):

    def _pruefen(self, karte):
        return technik.pruefen("https://x.test", falsches_netz(karte))

    def test_gesperrte_crawler_werden_gefunden(self):
        befunde, _ = self._pruefen({
            "x.test": (200, SEITE),
            "robots.txt": (200, "User-agent: *\nDisallow: /"),
        })
        crawler = [b for b in befunde if b.feld == "Crawler-Zugang"][0]
        self.assertFalse(crawler.bestanden)
        self.assertIn("PerplexityBot", crawler.aussage)

    def test_freie_seite_besteht(self):
        befunde, _ = self._pruefen({
            "x.test": (200, SEITE),
            "robots.txt": (200, "User-agent: *\nDisallow: /admin"),
        })
        crawler = [b for b in befunde if b.feld == "Crawler-Zugang"][0]
        self.assertTrue(crawler.bestanden)

    def test_leere_seite_faellt_schwer_ins_gewicht(self):
        befunde, _ = self._pruefen({
            "x.test": (200, "<html><body><div id=app></div></body></html>")})
        inhalt = [b for b in befunde if b.feld == "Lesbarer Inhalt"][0]
        self.assertFalse(inhalt.bestanden)
        self.assertEqual(inhalt.gewicht, 6)
        self.assertIn("JavaScript", inhalt.aussage)

    def test_nicht_erreichbar_bricht_sauber_ab(self):
        def kaputt(url, zeitlimit=None):
            return netz.Antwort(url, fehler="Domain nicht auffindbar (DNS)")
        befunde, leser = technik.pruefen("https://x.test", kaputt)
        self.assertEqual(len(befunde), 1)
        self.assertFalse(befunde[0].bestanden)
        self.assertIsNone(leser)

    def test_punkte_ignorieren_ungeprueftes(self):
        befunde = [technik.Befund("a", True, "", gewicht=2),
                   technik.Befund("b", False, "", gewicht=2),
                   technik.Befund("c", None, "", gewicht=90)]
        self.assertEqual(technik.punkte(befunde), (2, 4, 50))


class DomainTest(unittest.TestCase):

    def test_ergaenzt_schema(self):
        self.assertEqual(netz.domain_normalisieren("beispiel.ch"),
                         "https://beispiel.ch")

    def test_schneidet_pfad_ab(self):
        self.assertEqual(
            netz.domain_normalisieren("https://beispiel.ch/preise?a=1"),
            "https://beispiel.ch")

    def test_leere_eingabe(self):
        with self.assertRaises(ValueError):
            netz.domain_normalisieren("  ")


class FragenTest(unittest.TestCase):

    def test_wiederholbar(self):
        a = fragen.fragen_bauen("Treuhand", "Jona", ["Buchhaltung"])
        b = fragen.fragen_bauen("Treuhand", "Jona", ["Buchhaltung"])
        self.assertEqual(a, b)

    def test_keine_platzhalter_uebrig(self):
        for f in fragen.fragen_bauen("Treuhand", "Jona", ["Buchhaltung"]):
            self.assertNotIn("{", f)

    def test_ort_kommt_vor(self):
        liste = fragen.fragen_bauen("Treuhand", "Jona", ["Buchhaltung"])
        self.assertTrue(any("Jona" in f for f in liste))


class NennungTest(unittest.TestCase):

    def test_findet_firma(self):
        self.assertTrue(fragen.genannt(
            "Ich empfehle Meier Treuhand AG in Jona.", "Meier Treuhand AG"))

    def test_findet_ohne_rechtsform(self):
        self.assertTrue(fragen.genannt(
            "Meier Treuhand ist eine gute Wahl.", "Meier Treuhand AG"))

    def test_findet_ueber_domain(self):
        self.assertTrue(fragen.genannt(
            "Siehe meiertreuhand.ch fuer Details.", "Anders AG",
            "https://meiertreuhand.ch"))

    def test_keine_teiltreffer(self):
        # "Meier" darf nicht in "Meiernhof" treffen.
        self.assertFalse(fragen.genannt(
            "Der Meiernhof liegt in Jona.", "Meier"))

    def test_nicht_genannt(self):
        self.assertFalse(fragen.genannt(
            "Ich empfehle Muster Treuhand.", "Meier Treuhand AG"))


class ErhebungTest(unittest.TestCase):

    def setUp(self):
        self.datei = os.path.join(tempfile.mkdtemp(), "e.json")
        self.e = fragen.Erhebung(self.datei).anlegen(
            "Meier Treuhand AG", "https://meier.ch",
            ["Wer macht Buchhaltung in Jona?", "Was kostet das?"])

    def test_speichern_und_laden(self):
        self.e.sichern()
        wieder = fragen.Erhebung(self.datei)
        self.assertEqual(wieder.daten["firma"], "Meier Treuhand AG")
        self.assertEqual(len(wieder.daten["fragen"]), 2)

    def test_auswertung_zaehlt_echte_nennungen(self):
        self.e.erfassen("ChatGPT", "f1", "Ich empfehle Meier Treuhand AG.")
        self.e.erfassen("ChatGPT", "f2", "Ich empfehle Muster GmbH.")
        a = fragen.auswerten(self.e)
        self.assertEqual(a["gefragt"], 2)
        self.assertEqual(a["genannt"], 1)
        self.assertEqual(a["quote"], 50)

    def test_ohne_antworten_keine_quote(self):
        self.assertIsNone(fragen.auswerten(self.e)["quote"])


class BerichtTest(unittest.TestCase):

    def test_fremdtext_wird_escaped(self):
        # Ein Firmenname aus einer fremden Website landet im Bericht.
        b = [technik.Befund("Titel", True,
                            'Titel gesetzt: <script>alert("x")</script>')]
        seite = bericht.bauen('Meier & Co <AG>', "https://x.test", b,
                              (1, 1, 100))
        self.assertIn("&lt;script&gt;", seite)
        self.assertNotIn("<script>alert", seite)
        self.assertIn("Meier &amp; Co &lt;AG&gt;", seite)

    def test_ohne_erhebung_steht_nicht_erhoben_drin(self):
        seite = bericht.bauen("X", "https://x.test",
                              [technik.Befund("a", True, "ok")], (1, 1, 100))
        self.assertIn("Noch nicht erhoben", seite)
        self.assertNotIn("Die Antworten im Wortlaut", seite)


class CliTest(unittest.TestCase):

    def setUp(self):
        self.ordner = tempfile.mkdtemp()

    def test_fragen_legt_datei_an(self):
        datei = os.path.join(self.ordner, "e.json")
        code = cited.main(["fragen", "--firma", "Meier Treuhand AG",
                           "--domain", "meier.ch", "--branche", "Treuhand",
                           "--ort", "Jona", "--leistung", "Buchhaltung",
                           "--datei", datei])
        self.assertEqual(code, 0)
        with open(datei, encoding="utf-8") as f:
            daten = json.load(f)
        self.assertEqual(daten["domain"], "https://meier.ch")
        self.assertTrue(len(daten["fragen"]) >= 5)

    def test_erfassen_ohne_fragen_scheitert(self):
        datei = os.path.join(self.ordner, "leer.json")
        with open(datei, "w", encoding="utf-8") as f:
            json.dump({"firma": "X", "domain": "", "fragen": [],
                       "antworten": []}, f)
        antwort = os.path.join(self.ordner, "a.txt")
        with open(antwort, "w", encoding="utf-8") as f:
            f.write("irgendwas")
        self.assertEqual(cited.main(
            ["erfassen", "--datei", datei, "--system", "ChatGPT",
             "--frage", "1", "--antwort-datei", antwort]), 1)

    def test_erfassen_und_bericht(self):
        datei = os.path.join(self.ordner, "e.json")
        cited.main(["fragen", "--firma", "Meier Treuhand AG",
                    "--domain", "meier.ch", "--branche", "Treuhand",
                    "--ort", "Jona", "--leistung", "Buchhaltung",
                    "--datei", datei])
        antwort = os.path.join(self.ordner, "a.txt")
        with open(antwort, "w", encoding="utf-8") as f:
            f.write("Ich empfehle Meier Treuhand AG in Jona.")
        self.assertEqual(cited.main(
            ["erfassen", "--datei", datei, "--system", "ChatGPT",
             "--frage", "1", "--antwort-datei", antwort]), 0)
        with open(datei, encoding="utf-8") as f:
            self.assertEqual(len(json.load(f)["antworten"]), 1)

    def test_unbekannte_frage_nummer(self):
        datei = os.path.join(self.ordner, "e.json")
        cited.main(["fragen", "--firma", "X", "--domain", "x.ch",
                    "--branche", "B", "--ort", "O", "--leistung", "L",
                    "--datei", datei])
        antwort = os.path.join(self.ordner, "a.txt")
        with open(antwort, "w", encoding="utf-8") as f:
            f.write("x")
        self.assertEqual(cited.main(
            ["erfassen", "--datei", datei, "--system", "ChatGPT",
             "--frage", "99", "--antwort-datei", antwort]), 1)


if __name__ == "__main__":
    unittest.main()
