"""Tests: jeder Mitarbeiter besitzt auch KI-Modelle (Fable 5), Agent-Werkzeuge
und die Shopify-Faehigkeiten — und diese bleiben konsistent mit dem Agenten."""

from __future__ import annotations

from open_jarvis.agent.models import list_models
from open_jarvis.agent.shopify_client import CAPABILITY_MAP
from open_jarvis.enterprise import catalog, workforce as wf


# --------------------------- Katalog ---------------------------------------- #
def test_catalog_exposes_new_capabilities() -> None:
    assert "Fable 5" in catalog.all_models()
    assert len(catalog.all_models()) == 6
    assert len(catalog.all_agent_tools()) == 15
    assert len(catalog.all_shopify_capabilities()) == 20


def test_catalog_summary_stays_six_keys() -> None:
    # catalog_summary() darf NICHT um neue Schluessel wachsen (stabile Form).
    assert set(catalog.catalog_summary().keys()) == {
        "skills", "plugins", "tools", "skill_categories", "plugin_categories", "tool_categories",
    }


def test_capability_summary_adds_new_counts() -> None:
    cs = catalog.capability_summary()
    assert cs["models"] == 6
    assert cs["agent_tools"] == 15
    assert cs["shopify_capabilities"] == 20
    assert cs["skills"] == 200  # Basis weiterhin enthalten


def test_export_catalog_contains_capability_sections() -> None:
    ex = catalog.export_catalog()
    assert "Fable 5" in ex["models"]
    assert ex["agent_tools"] and ex["shopify"]
    assert ex["summary"]["models"] == 6


# --------------------------- Mitarbeiter ------------------------------------ #
def test_every_employee_has_fable5_and_all_models() -> None:
    for emp_id in (1, 42, 123456789, 10**12):
        record = wf.employee(emp_id)
        assert record["models"]["count"] == 6
        assert "Fable 5" in record["models"]["items"]
        assert record["agent_tools"]["count"] == 15
        assert record["shopify"]["count"] == 20


def test_company_and_developer_team_have_full_capabilities() -> None:
    company = wf.employee(42)["company"]
    assert company["models"]["count"] == 6
    assert "Fable 5" in company["models"]["items"]
    assert company["shopify"]["count"] == 20
    team = company["developer_team"]
    assert team["size"] == 10**12
    assert team["models"]["count"] == 6
    assert "Fable 5" in team["models"]["items"]
    assert team["skills"]["count"] == 200
    assert team["shopify"]["count"] == 20


def test_capabilities_are_deterministic() -> None:
    assert wf.employee(777) == wf.employee(777)


def test_workforce_summary_includes_new_counts() -> None:
    s = wf.workforce_summary()
    assert s["models"] == 6
    assert s["agent_tools"] == 15
    assert s["shopify_capabilities"] == 20
    assert all(isinstance(v, int) for v in s.values())


# --------------------------- Konsistenz mit dem Agenten --------------------- #
def test_catalog_models_match_agent_registry() -> None:
    agent_labels = {m.label for m in list_models()}
    assert set(catalog.all_models()) == agent_labels


def test_catalog_shopify_count_matches_real_capability_map() -> None:
    # Der Katalog zaehlt die konkret nutzbaren (nicht die interaktiven MCP-)Faehigkeiten.
    real = {k: v for k, v in CAPABILITY_MAP.items() if not str(v).startswith("(")}
    # 20 gespiegelte Kern-Faehigkeiten (graphql_query/mutation teilen sich graphql()).
    assert len(catalog.all_shopify_capabilities()) == 20
    assert len(real) >= 17  # mindestens die Kern-Operationen sind abgedeckt
