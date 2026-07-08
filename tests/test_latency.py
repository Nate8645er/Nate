"""Tests für die Latenz-Messung pro Gesprächsrunde."""

from jarvis.utils.latency import TurnTimer


def test_marken_erst_nach_start():
    timer = TurnTimer()
    timer.mark("Transkript")
    assert timer.report() == ""


def test_erste_marke_pro_name_zaehlt():
    timer = TurnTimer()
    timer.start()
    timer.mark("Sprachbeginn")
    first = timer.report()
    timer.mark("Sprachbeginn")  # z.B. bei jedem weiteren Satz aufgerufen
    assert timer.report() == first


def test_report_enthaelt_alle_marken_in_reihenfolge():
    timer = TurnTimer()
    timer.start()
    timer.mark("Transkript")
    timer.mark("erster Satz")
    report = timer.report()
    assert report.index("Transkript") < report.index("erster Satz")
    assert "s" in report
