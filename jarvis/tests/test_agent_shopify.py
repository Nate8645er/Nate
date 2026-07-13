"""Tests fuer die Shopify-Anbindung des JARVIS-Agenten (gemockt, kein Netz)."""

from __future__ import annotations

import pytest

from open_jarvis.agent.shop_builder import build_shop_blueprint
from open_jarvis.agent.shopify_client import (
    CAPABILITY_MAP,
    ShopifyClient,
    normalize_store,
    publish_blueprint,
)
from open_jarvis.agent.shopify_client import _num
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


# --------------------------- MCP-gespiegelte Faehigkeiten ------------------- #
def test_capability_map_covers_core_mcp_tools() -> None:
    for mcp_tool in [
        "get-shop-info", "search_products", "get-product", "create-product",
        "update-product", "bulk-update-product-status", "create-collection",
        "add-to-collection", "list-orders", "get-order", "list-customers",
        "get-inventory-levels", "set-inventory", "create-discount",
        "run-analytics-query", "graphql_query", "graphql_mutation",
    ]:
        assert mcp_tool in CAPABILITY_MAP


@pytest.mark.parametrize(
    "raw,expected",
    [(123, "123"), ("123", "123"), ("gid://shopify/Product/123", "123"), ("gid://shopify/Order/9/", "9")],
)
def test_num_accepts_gid_and_int(raw, expected) -> None:
    assert _num(raw) == expected


def _recording_transport(routes):
    calls = []

    def transport(method, url, payload, headers):
        calls.append((method, url, payload))
        for suffix, response in routes.items():
            if url.endswith(suffix):
                return response
        return {}

    return transport, calls


def test_client_read_methods_hit_expected_endpoints() -> None:
    routes = {
        "/shop.json": {"shop": {"name": "My Store", "domain": "x.myshopify.com"}},
        "/products.json?limit=10": {"products": [{"title": "A"}, {"title": "B"}]},
        "/orders.json?limit=5&status=any": {"orders": [{"name": "#1001"}]},
        "/customers.json?limit=10": {"customers": [{"email": "a@b.c"}]},
    }
    transport, calls = _recording_transport(routes)
    client = ShopifyClient(store="my-store", token="tok", transport=transport)
    assert client.get_shop()["name"] == "My Store"
    assert len(client.search_products(first=10)) == 2
    assert len(client.list_orders(first=5)) == 1
    assert len(client.list_customers(first=10)) == 1
    assert any(url.endswith("/shop.json") for _, url, _ in calls)


def test_create_discount_creates_rule_and_code() -> None:
    routes = {
        "/price_rules.json": {"price_rule": {"id": 55, "title": "SOMMER20"}},
        "/price_rules/55/discount_codes.json": {"discount_code": {"id": 77, "code": "SOMMER20"}},
    }
    transport, calls = _recording_transport(routes)
    client = ShopifyClient(store="my-store", token="tok", transport=transport)
    result = client.create_discount(code="SOMMER20", percentage=20)
    assert result["discount_code"]["code"] == "SOMMER20"
    assert result["percentage"] == 20.0
    # Wert muss negativ-prozentual sein.
    rule_call = next(p for m, u, p in calls if u.endswith("/price_rules.json"))
    assert rule_call["price_rule"]["value"] == "-20.0"


def test_read_methods_require_credentials() -> None:
    client = ShopifyClient(store="", token="")
    from open_jarvis.agent.shopify_client import ShopifyError

    for call in (client.get_shop, client.list_orders, client.search_products):
        with pytest.raises(ShopifyError):
            call()


def test_tool_shop_info_and_rabatt_report_missing_credentials(tmp_path) -> None:
    reg = build_default_registry()
    ctx = ToolContext(workspace=tmp_path, shopify=ShopifyClient(store="", token=""))
    assert reg["shop_info"].handler({}, ctx).ok is False
    assert reg["shop_rabatt"].handler({"code": "X10", "percentage": 10}, ctx).ok is False


def test_tool_shop_rabatt_executes_with_client(tmp_path) -> None:
    routes = {
        "/price_rules.json": {"price_rule": {"id": 5}},
        "/price_rules/5/discount_codes.json": {"discount_code": {"id": 9, "code": "X10"}},
    }
    transport, _ = _recording_transport(routes)
    client = ShopifyClient(store="s", token="t", transport=transport)
    reg = build_default_registry()
    ctx = ToolContext(workspace=tmp_path, execute=True, shopify=client)
    result = reg["shop_rabatt"].handler({"code": "X10", "percentage": 10}, ctx)
    assert result.ok and result.executed
    assert result.data["discount_code_id"] == 9
