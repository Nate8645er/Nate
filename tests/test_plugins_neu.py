"""Tests für die neuen Plugins: Notizen, Zufall, Passwort, Einheiten."""

from jarvis.plugins.einheiten import EinheitenPlugin
from jarvis.plugins.notizen import NotizenPlugin
from jarvis.plugins.passwort import PasswortPlugin
from jarvis.plugins.zufall import ZufallPlugin


def test_notizen_anlegen_anzeigen_loeschen(tmp_path):
    plugin = NotizenPlugin(storage_file=tmp_path / "notizen.json")
    assert "Nr. 1" in plugin.execute("notiz", "Milch kaufen")
    assert "Nr. 2" in plugin.execute("notiz", "Zahnarzt anrufen")
    uebersicht = plugin.execute("notizen", "")
    assert "Milch kaufen" in uebersicht and "Zahnarzt" in uebersicht
    assert "Gelöscht: Milch kaufen" in plugin.execute("notiz-weg", "1")
    assert "Milch" not in plugin.execute("notizen", "")
    assert "gelöscht" in plugin.execute("notiz-weg", "alles")


def test_notizen_ueberleben_neustart(tmp_path):
    datei = tmp_path / "notizen.json"
    NotizenPlugin(storage_file=datei).execute("notiz", "bleibt da")
    neu_geladen = NotizenPlugin(storage_file=datei)
    assert "bleibt da" in neu_geladen.execute("notizen", "")


def test_wuerfel_bleibt_im_bereich():
    plugin = ZufallPlugin()
    for _ in range(50):
        zahl = int(plugin.execute("wuerfel", "20").split(":")[-1])
        assert 1 <= zahl <= 20
    assert "mindestens 2" in plugin.execute("wuerfel", "1")


def test_muenze_und_entscheidung():
    plugin = ZufallPlugin()
    assert any(w in plugin.execute("muenze", "") for w in ("Kopf", "Zahl"))
    antwort = plugin.execute("entscheide", "Pizza, Pasta, Salat")
    assert any(o in antwort for o in ("Pizza", "Pasta", "Salat"))
    assert "Nutzung" in plugin.execute("entscheide", "nur-eine-option")


def test_passwort_laenge_und_vielfalt():
    plugin = PasswortPlugin()
    antwort = plugin.execute("passwort", "24")
    pw = antwort.split("\n")[1].strip()
    assert len(pw) == 24
    assert "Nutzung" in plugin.execute("passwort", "4")  # zu kurz


def test_einheiten_umrechnen():
    plugin = EinheitenPlugin()
    assert "3.11" in plugin.execute("umrechnen", "5 km in meilen")
    assert "86.00 °F" in plugin.execute("umrechnen", "30 celsius in fahrenheit")
    assert "kenne ich nicht" in plugin.execute("umrechnen", "5 km in kg")
    assert "Nutzung" in plugin.execute("umrechnen", "kaputt")
