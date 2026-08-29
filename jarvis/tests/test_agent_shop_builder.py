"""Tests fuer den deterministischen Shop-Bauplan-Generator."""

from __future__ import annotations

from open_jarvis.agent.shop_builder import build_shop_blueprint, slugify


def test_blueprint_is_deterministic() -> None:
    a = build_shop_blueprint(name="Bergbohne", sells="Kaffee", audience="Kenner", style="warm")
    b = build_shop_blueprint(name="Bergbohne", sells="Kaffee", audience="Kenner", style="warm")
    assert a == b


def test_blueprint_structure_and_counts() -> None:
    bp = build_shop_blueprint(name="Wachswerk", sells="Kerzen", product_count=8)
    assert bp["name"] == "Wachswerk"
    assert bp["slug"] == "wachswerk"
    assert len(bp["products"]) == 8
    assert len(bp["collections"]) == 3
    assert bp["palette"]["background"].startswith("#")
    assert "# Wachswerk" in bp["markdown"]
    assert bp["checklist"]


def test_product_prices_and_skus() -> None:
    bp = build_shop_blueprint(name="Test Shop", sells="Dinge", product_count=5)
    for product in bp["products"]:
        price = float(product["price_chf"])
        assert 18.0 <= price <= 199.0
        assert product["sku"].startswith("TESTSH")
        assert product["collection"] in {c["title"] for c in bp["collections"]}


def test_product_count_is_clamped() -> None:
    assert len(build_shop_blueprint(name="x", sells="y", product_count=1)["products"]) == 3
    assert len(build_shop_blueprint(name="x", sells="y", product_count=999)["products"]) == 24


def test_slugify_handles_umlauts_and_symbols() -> None:
    assert slugify("Grüße & Co!") == "gruesse-co"
    assert slugify("") == "mein-shop"
