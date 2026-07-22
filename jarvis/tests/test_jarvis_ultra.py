"""Tests for the jarvis_ultra catalog, mega-org simulation, and live ticker."""

from __future__ import annotations

import json

from jarvis_ultra import catalog, live_ticker, mega_org

N = mega_org.EMPLOYEES_PER_COMPANY
D = mega_org.DEVELOPERS_PER_COMPANY


def test_catalog_sizes_and_summary() -> None:
    assert len(catalog.all_plugins()) == 16
    assert len(catalog.all_skills()) == 50
    assert len(catalog.all_tools()) == 18
    assert catalog.loadout_size() == 84
    assert catalog.loadout_summary() == "16 Plugins · 50 Skills · 18 Tools — alle aktiv"


def test_employee_is_deterministic_and_distinct() -> None:
    once = mega_org.employee((7, 42), seed=3)
    twice = mega_org.employee((7, 42), seed=3)
    other = mega_org.employee((7, 43), seed=3)
    assert once == twice
    assert once["id"] == "E-7.42"
    assert once != other


def test_company_is_deterministic_and_owned() -> None:
    firm = mega_org.company((987_654_321_098,))
    assert firm == mega_org.company((987_654_321_098,))
    assert firm["owner_id"] == "E-987654321098"
    assert firm["employees"] == N
    assert firm["developers"] == D


def test_everyone_has_the_full_loadout() -> None:
    for entity in [mega_org.employee((0,)), mega_org.company((5, 5))] + mega_org.sample_employees(5, depth=2):
        assert catalog.has_full_loadout(entity)
        assert len(entity["loadout"]["plugins"]) == 16
        assert len(entity["loadout"]["skills"]) == 50
        assert len(entity["loadout"]["tools"]) == 18


def test_org_totals_exact_math() -> None:
    depth1 = mega_org.org_totals(1)
    assert depth1["total_employees"] == N
    assert depth1["total_companies"] == N
    assert depth1["total_developers"] == N * D
    assert depth1["total_members"] == 1 + N + N * D

    depth2 = mega_org.org_totals(2)
    assert depth2["total_employees"] == N + N**2
    assert depth2["total_developers"] == (N + N**2) * D
    assert depth2["total_loadout_items"] == depth2["total_members"] * 84


def test_sample_employees_deterministic() -> None:
    assert mega_org.sample_employees(4, depth=3, seed=9) == mega_org.sample_employees(4, depth=3, seed=9)
    assert all(item["depth"] == 3 for item in mega_org.sample_employees(4, depth=3, seed=9))


def test_format_big_german() -> None:
    assert mega_org.format_big(1234) == "1.234"
    assert mega_org.format_big(10**12) == "1 Billion (1.000.000.000.000)"
    assert mega_org.format_big(5 * 10**24).startswith("5 Quadrillionen")
    assert mega_org.format_big(10**36).startswith("1 Sextillion")


def test_live_ticker_json_mode(capsys) -> None:
    assert live_ticker.main(["--ticks", "3", "--interval", "0", "--json", "--seed", "7"]) == 0
    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    assert lines
    for line in lines:
        event = json.loads(line)
        assert event["type"] in live_ticker.EVENT_TYPES
        assert event["employee_id"].startswith("E-")


def test_live_ticker_pretty_mode_has_aggregates(capsys) -> None:
    assert live_ticker.main(["--ticks", "2", "--interval", "0"]) == 0
    out = capsys.readouterr().out
    assert "[TICK 0000]" in out
    assert "MEGA-ORG GESAMTSTAND" in out
    assert "≈ 10^" in out
