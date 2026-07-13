"""Tests fuer die Shopify-Anbindung des JARVIS-Agenten (gemockt, kein Netz)."""

from __future__ import annotations

import pytest

from open_jarvis.agent.shop_builder import build_shop_blueprint
from open_jarvis.agent.shopify_client import ShopifyClient, normalize_store, publish_blueprint
from open_jarvis.agent.tools import ToolContext, build_default_registry


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("bergbohne", "bergbohne.myshopify.com"),
        ("bergbohne.myshopify.com", "bergbohne.myshopify.com"),
        ("https://bergbohne.myshopify.com/", "bergbohne.myshopify.com"),
        ("", ""),
    ],
)
def test_normalize_store(raw, expected) -> None:
    assert normalize_store(raw) == expected


def test_client_unavailable_without_credentials() -> None:
    assert ShopifyClient(store="", token="").available() is False
    assert ShopifyClient(store="shop", token="").available() is False
    assert ShopifyClient(store="shop", token="tok").available() is True


def _mock_transport(recorder):
    def transport(method, url, payload, headers):
        recorder.append((method, url))
        assert headers["X-Shopify-Access-Token"] == "tok"
        if url.endswith("/products.json"):
            # Produkte muessen als Entwurf angelegt werden.
            assert payload["product"]["status"] == "draft"
            return {"product": {"id": 111, "title": payload["product"]["title"]}}
        if url.endswith("/custom_collections.json"):
            return {"custom_collection": {"id": 222, "title": payload["custom_collection"]["title"]}}
        return {}
    return transport


def test_publish_blueprint_creates_products_and_collections() -> None:
    calls: list = []
    client = ShopifyClient(store="bergbohne", token="tok", transport=_mock_transport(calls))
    blueprint = build_shop_blueprint(name="Bergbohne", sells="Kaffee", product_count=5)
    result = publish_blueprint(blueprint, client)
    assert result.ok
    assert len(result.created_products) == 5
    assert len(result.created_collections) == 3
    assert any(url.endswith("/products.json") for _, url in calls)


def test_publish_blueprint_without_credentials_is_clear() -> None:
    result = publish_blueprint(build_shop_blueprint(name="X", sells="y"), ShopifyClient(store="", token=""))
    assert result.ok is False
    assert "SHOPIFY_STORE" in result.summary


def test_tool_veroeffentlichen_preview_without_execute() -> None:
    calls: list = []
    client = ShopifyClient(store="bergbohne", token="tok", transport=_mock_transport(calls))
    reg = build_default_registry()
    ctx = ToolContext(workspace=__import__("pathlib").Path("/tmp"), execute=False, shopify=client)
    result = reg["shop_veroeffentlichen"].handler({"name": "Bergbohne", "sells": "Kaffee"}, ctx)
    assert result.ok
    assert result.executed is False
    assert calls == []  # Vorschau ruft die API nicht auf


def test_tool_veroeffentlichen_executes_with_client(tmp_path) -> None:
    calls: list = []
    client = ShopifyClient(store="bergbohne", token="tok", transport=_mock_transport(calls))
    reg = build_default_registry()
    ctx = ToolContext(workspace=tmp_path, execute=True, shopify=client)
    result = reg["shop_veroeffentlichen"].handler({"name": "Bergbohne", "sells": "Kaffee"}, ctx)
    assert result.ok
    assert result.executed
    assert result.data["created_products"]
    assert calls  # API wurde aufgerufen


def test_tool_veroeffentlichen_reports_missing_credentials(tmp_path) -> None:
    reg = build_default_registry()
    ctx = ToolContext(workspace=tmp_path, execute=True, shopify=ShopifyClient(store="", token=""))
    result = reg["shop_veroeffentlichen"].handler({"name": "X", "sells": "y"}, ctx)
    assert result.ok is False
    assert "SHOPIFY_STORE" in result.summary
