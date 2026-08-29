"""Shopify-Admin-Anbindung fuer den JARVIS-Agenten.

Spiegelt den Funktionsumfang des Shopify-MCP-Werkzeugsatzes in JARVIS: Produkte,
Kollektionen, Bestellungen, Kunden, Inventar, Rabatte, Analytics und ein
generischer GraphQL-Zugang. Verwendet nur ``requests`` (bereits JARVIS-
Abhaengigkeit) gegen die Shopify-Admin-API (REST + GraphQL).

Ehrlich & sicher:
- Braucht zwei Zugangsdaten in Umgebungsvariablen: ``SHOPIFY_STORE`` (z. B.
  ``mein-shop`` oder ``mein-shop.myshopify.com``) und ``SHOPIFY_ADMIN_TOKEN``.
- Fehlen sie, meldet ``available() == False`` und der Agent bleibt im Bauplan-Modus.
- Neu erstellte Produkte sind standardmaessig ``draft`` (nicht sofort oeffentlich).
- ``CAPABILITY_MAP`` dokumentiert, welches MCP-Werkzeug welcher Methode entspricht.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

DEFAULT_API_VERSION = "2024-10"
DEFAULT_TIMEOUT = 30

# Zuordnung Shopify-MCP-Werkzeug -> JARVIS-ShopifyClient-Methode (Doku & Tests).
CAPABILITY_MAP: dict[str, str] = {
    "get-shop-info": "get_shop",
    "search_products": "search_products",
    "get-product": "get_product",
    "create-product": "create_product",
    "update-product": "update_product",
    "bulk-update-product-status": "bulk_update_product_status",
    "search_collections": "search_collections",
    "get-collection": "get_collection",
    "create-collection": "create_collection",
    "update-collection": "update_collection",
    "add-to-collection": "add_to_collection",
    "list-orders": "list_orders",
    "get-order": "get_order",
    "list-customers": "list_customers",
    "get-inventory-levels": "get_inventory_levels",
    "set-inventory": "set_inventory",
    "create-discount": "create_discount",
    "run-analytics-query": "run_analytics_query",
    "graphql_query": "graphql",
    "graphql_mutation": "graphql",
    # Nur im interaktiven MCP verfuegbar (kein reiner Admin-API-Aufruf):
    "get-new-store-previews": "(nur ueber Shopify-MCP / claude.ai)",
    "switch-shop": "(Store via SHOPIFY_STORE waehlen)",
    "graphql_schema": "(Entwickler-Hilfe im MCP)",
    "validate_graphql_codeblocks": "(Entwickler-Hilfe im MCP)",
    "search_docs_chunks": "(Entwickler-Hilfe im MCP)",
}


class ShopifyError(RuntimeError):
    """Fehler bei einem Shopify-API-Aufruf."""


def normalize_store(store: str) -> str:
    """'mein-shop' oder 'mein-shop.myshopify.com' -> 'mein-shop.myshopify.com'."""

    value = (store or "").strip().lower()
    value = value.replace("https://", "").replace("http://", "").rstrip("/")
    if not value:
        return ""
    if not value.endswith(".myshopify.com"):
        value = f"{value.split('.')[0]}.myshopify.com"
    return value


@dataclass
class ShopifyResult:
    ok: bool
    summary: str
    created_products: list[dict[str, Any]] = field(default_factory=list)
    created_collections: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "created_products": self.created_products,
            "created_collections": self.created_collections,
            "errors": self.errors,
        }


class ShopifyClient:
    """Admin-Client (REST + GraphQL), testbar ueber einen injizierten Transport."""

    def __init__(
        self,
        *,
        store: str | None = None,
        token: str | None = None,
        api_version: str = DEFAULT_API_VERSION,
        transport: Any = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.store = normalize_store(store if store is not None else os.getenv("SHOPIFY_STORE", ""))
        self.token = (token if token is not None else os.getenv("SHOPIFY_ADMIN_TOKEN", "")).strip()
        self.api_version = api_version
        self._transport = transport  # (method, url, payload, headers) -> dict; sonst requests
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.store and self.token)

    # ------------------------------------------------------------------ intern
    def _base(self) -> str:
        return f"https://{self.store}/admin/api/{self.api_version}"

    def _headers(self) -> dict[str, str]:
        return {"X-Shopify-Access-Token": self.token, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base()}{path}"
        headers = self._headers()
        if self._transport is not None:
            return self._transport(method, url, payload, headers) or {}
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise ShopifyError("Das Paket 'requests' ist nicht installiert.") from exc
        response = requests.request(method, url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code >= 400:
            raise ShopifyError(f"Shopify-API-Fehler {response.status_code}")
        return response.json() if response.content else {}

    def _require(self) -> None:
        if not self.available():
            raise ShopifyError("Keine Shopify-Zugangsdaten (SHOPIFY_STORE + SHOPIFY_ADMIN_TOKEN).")

    # ------------------------------------------------------------------ Shop
    def get_shop(self) -> dict[str, Any]:
        self._require()
        return self._request("GET", "/shop.json").get("shop", {})

    # ------------------------------------------------------------------ GraphQL
    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generischer Admin-GraphQL-Zugang (entspricht graphql_query/graphql_mutation)."""

        self._require()
        return self._request("POST", "/graphql.json", {"query": query, "variables": variables or {}})

    def run_analytics_query(self, shopifyql: str) -> dict[str, Any]:
        """ShopifyQL-Analytics ueber GraphQL (entspricht run-analytics-query)."""

        query = "query($q: String!) { shopifyqlQuery(query: $q) { __typename ... on TableResponse { tableData { rowData columns { name } } } } }"
        return self.graphql(query, {"q": shopifyql})

    # ------------------------------------------------------------------ Produkte
    def search_products(self, query: str = "", first: int = 10) -> list[dict[str, Any]]:
        self._require()
        params = f"?limit={max(1, min(50, first))}"
        if query:
            params += f"&title={query}"
        return self._request("GET", f"/products.json{params}").get("products", [])

    def get_product(self, product_id: str | int) -> dict[str, Any]:
        self._require()
        return self._request("GET", f"/products/{_num(product_id)}.json").get("product", {})

    def create_product(self, *, title: str, body_html: str = "", price: str = "0.00", sku: str = "", status: str = "draft") -> dict[str, Any]:
        self._require()
        variant = {"price": str(price)}
        if sku:
            variant["sku"] = sku
        payload = {"product": {"title": title, "body_html": body_html, "status": status, "variants": [variant]}}
        return self._request("POST", "/products.json", payload).get("product", {})

    def update_product(self, product_id: str | int, *, title: str | None = None, body_html: str | None = None, status: str | None = None) -> dict[str, Any]:
        self._require()
        product: dict[str, Any] = {"id": _num(product_id)}
        if title is not None:
            product["title"] = title
        if body_html is not None:
            product["body_html"] = body_html
        if status is not None:
            product["status"] = status
        return self._request("PUT", f"/products/{_num(product_id)}.json", {"product": product}).get("product", {})

    def bulk_update_product_status(self, product_ids: list[str | int], status: str) -> list[dict[str, Any]]:
        return [self.update_product(pid, status=status) for pid in product_ids]

    # ------------------------------------------------------------------ Kollektionen
    def search_collections(self, first: int = 10) -> list[dict[str, Any]]:
        self._require()
        return self._request("GET", f"/custom_collections.json?limit={max(1, min(50, first))}").get("custom_collections", [])

    def get_collection(self, collection_id: str | int) -> dict[str, Any]:
        self._require()
        return self._request("GET", f"/custom_collections/{_num(collection_id)}.json").get("custom_collection", {})

    def create_collection(self, *, title: str, body_html: str = "") -> dict[str, Any]:
        self._require()
        return self._request("POST", "/custom_collections.json", {"custom_collection": {"title": title, "body_html": body_html}}).get("custom_collection", {})

    def update_collection(self, collection_id: str | int, *, title: str | None = None, body_html: str | None = None) -> dict[str, Any]:
        self._require()
        col: dict[str, Any] = {"id": _num(collection_id)}
        if title is not None:
            col["title"] = title
        if body_html is not None:
            col["body_html"] = body_html
        return self._request("PUT", f"/custom_collections/{_num(collection_id)}.json", {"custom_collection": col}).get("custom_collection", {})

    def add_to_collection(self, collection_id: str | int, product_ids: list[str | int]) -> list[dict[str, Any]]:
        self._require()
        results = []
        for pid in product_ids:
            payload = {"collect": {"product_id": _num(pid), "collection_id": _num(collection_id)}}
            results.append(self._request("POST", "/collects.json", payload).get("collect", {}))
        return results

    # ------------------------------------------------------------------ Bestellungen / Kunden
    def list_orders(self, first: int = 10, status: str = "any") -> list[dict[str, Any]]:
        self._require()
        return self._request("GET", f"/orders.json?limit={max(1, min(50, first))}&status={status}").get("orders", [])

    def get_order(self, order_id: str | int) -> dict[str, Any]:
        self._require()
        return self._request("GET", f"/orders/{_num(order_id)}.json").get("order", {})

    def list_customers(self, first: int = 10, query: str = "") -> list[dict[str, Any]]:
        self._require()
        if query:
            return self._request("GET", f"/customers/search.json?query={query}&limit={max(1, min(50, first))}").get("customers", [])
        return self._request("GET", f"/customers.json?limit={max(1, min(50, first))}").get("customers", [])

    # ------------------------------------------------------------------ Inventar
    def get_inventory_levels(self, inventory_item_ids: list[str | int]) -> list[dict[str, Any]]:
        self._require()
        ids = ",".join(str(_num(i)) for i in inventory_item_ids)
        return self._request("GET", f"/inventory_levels.json?inventory_item_ids={ids}").get("inventory_levels", [])

    def set_inventory(self, *, inventory_item_id: str | int, location_id: str | int, available: int) -> dict[str, Any]:
        self._require()
        payload = {"location_id": _num(location_id), "inventory_item_id": _num(inventory_item_id), "available": int(available)}
        return self._request("POST", "/inventory_levels/set.json", payload).get("inventory_level", {})

    # ------------------------------------------------------------------ Rabatte
    def create_discount(self, *, code: str, percentage: float, title: str | None = None, starts_at: str | None = None) -> dict[str, Any]:
        """Prozent-Rabattcode ueber Price-Rules + Discount-Codes (entspricht create-discount)."""

        self._require()
        pct = max(1.0, min(100.0, float(percentage)))
        rule_payload = {
            "price_rule": {
                "title": title or code,
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": "percentage",
                "value": f"-{pct:.1f}",
                "customer_selection": "all",
                "starts_at": starts_at or "2020-01-01T00:00:00Z",
            }
        }
        rule = self._request("POST", "/price_rules.json", rule_payload).get("price_rule", {})
        rule_id = rule.get("id")
        code_obj = {}
        if rule_id is not None:
            code_obj = self._request("POST", f"/price_rules/{rule_id}/discount_codes.json", {"discount_code": {"code": code}}).get("discount_code", {})
        return {"price_rule": rule, "discount_code": code_obj, "percentage": pct}


def _num(gid_or_id: str | int) -> str:
    """Akzeptiert Zahl oder GID (gid://shopify/Product/123) -> nackte Zahl als String."""

    text = str(gid_or_id).strip()
    if "/" in text:
        text = text.rstrip("/").split("/")[-1]
    return text


def publish_blueprint(blueprint: dict[str, Any], client: ShopifyClient) -> ShopifyResult:
    """Einen Shop-Bauplan live in Shopify anlegen (Produkte als draft)."""

    if not client.available():
        return ShopifyResult(
            ok=False,
            summary="Keine Shopify-Zugangsdaten. Setze SHOPIFY_STORE und SHOPIFY_ADMIN_TOKEN, "
            "um den Shop wirklich live anzulegen.",
        )
    result = ShopifyResult(ok=True, summary="")
    try:
        for col in blueprint.get("collections", []):
            created = client.create_collection(title=col["title"], body_html=col.get("description", ""))
            result.created_collections.append({"title": col["title"], "id": created.get("id")})
        for product in blueprint.get("products", []):
            created = client.create_product(
                title=product["title"],
                body_html=product.get("description", ""),
                price=product["price_chf"],
                sku=product.get("sku", ""),
                status="draft",
            )
            result.created_products.append({"title": product["title"], "id": created.get("id")})
    except ShopifyError as exc:
        result.ok = False
        result.errors.append(str(exc))
    result.summary = (
        f"{len(result.created_products)} Produkte und {len(result.created_collections)} "
        f"Kollektionen in Shopify angelegt (Produkte als Entwurf)."
        if result.ok
        else f"Teilweise fehlgeschlagen: {'; '.join(result.errors)}"
    )
    return result
