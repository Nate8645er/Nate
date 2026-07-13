"""Shopify-Admin-API-Client fuer den JARVIS-Agenten.

Ermoeglicht dem Agenten, aus einem Shop-Bauplan echte Produkte und Kollektionen
in einem Shopify-Store anzulegen.

Verwendet nur ``requests`` (bereits JARVIS-Abhaengigkeit) und die Admin-REST-API.

Ehrlich & sicher: Braucht zwei Zugangsdaten in Umgebungsvariablen —
``SHOPIFY_STORE`` (z. B. ``mein-shop`` oder ``mein-shop.myshopify.com``) und
``SHOPIFY_ADMIN_TOKEN`` (Admin-API-Zugriffstoken). Fehlen sie, meldet der Client
sauber ``available() == False`` und der Agent bleibt im Bauplan-Modus.
Produkte werden standardmaessig als ``draft`` angelegt, damit nichts
versehentlich sofort oeffentlich verkauft wird.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

DEFAULT_API_VERSION = "2024-10"
DEFAULT_TIMEOUT = 30


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
    """Duenner Admin-REST-Client, testbar ueber einen injizierten Transport."""

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

    def _base(self) -> str:
        return f"https://{self.store}/admin/api/{self.api_version}"

    def _headers(self) -> dict[str, str]:
        return {"X-Shopify-Access-Token": self.token, "Content-Type": "application/json"}

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base()}{path}"
        headers = self._headers()
        if self._transport is not None:
            return self._transport(method, url, payload, headers)
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise ShopifyError("Das Paket 'requests' ist nicht installiert.") from exc
        response = requests.request(method, url, json=payload, headers=headers, timeout=self.timeout)
        if response.status_code >= 400:
            raise ShopifyError(f"Shopify-API-Fehler {response.status_code}")
        return response.json() if response.content else {}

    # ------------------------------------------------------------------ API
    def get_shop(self) -> dict[str, Any]:
        return self._request("GET", "/shop.json").get("shop", {})

    def create_product(self, *, title: str, body_html: str, price: str, sku: str = "", status: str = "draft") -> dict[str, Any]:
        payload = {
            "product": {
                "title": title,
                "body_html": body_html,
                "status": status,
                "variants": [{"price": str(price), "sku": sku} if sku else {"price": str(price)}],
            }
        }
        return self._request("POST", "/products.json", payload).get("product", {})

    def create_collection(self, *, title: str, body_html: str = "") -> dict[str, Any]:
        payload = {"custom_collection": {"title": title, "body_html": body_html}}
        return self._request("POST", "/custom_collections.json", payload).get("custom_collection", {})


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
