"""Werkzeug-Registry fuer den JARVIS-Agenten.

Das ist die Sammlung echter Faehigkeiten, die der Agent aufrufen kann — analog
zu den Werkzeugen von Claude Code, aber sicher auf JARVIS zugeschnitten:

- ``web_suche``      Websuche vorbereiten (sichere Google-URL)
- ``webseite``       Webseite/Link oeffnen (URL-Sicherheitspruefung)
- ``app_starten``    Desktop-App starten (Befehl fuer den Action-Dispatcher)
- ``datei_schreiben``Datei im Arbeitsbereich anlegen (echt, pfadsicher)
- ``datei_lesen``    Datei im Arbeitsbereich lesen (echt, pfadsicher)
- ``notiz``          Notiz/Erinnerung ablegen
- ``shop_bauen``     Kompletten, verkaufsfertigen Shop-Bauplan erzeugen (echt)
- ``plugins``        Verfuegbare JARVIS-Plugins auflisten (aus dem Katalog)

Sicherheit: Datei-Werkzeuge bleiben strikt im Arbeitsbereich (``path_safety``),
es gibt keine beliebige Shell-Ausfuehrung. Werkzeuge laufen entweder im Modus
``plan`` (Vorschau, nichts wird veraendert) oder ``execute`` (echte Wirkung).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from open_jarvis.integrations.url_safety import build_google_search_url, normalize_web_url
from open_jarvis.security.path_safety import validate_path_within_root

from open_jarvis.agent.shop_builder import build_shop_blueprint
from open_jarvis.agent.shopify_client import ShopifyClient, publish_blueprint


@dataclass(frozen=True)
class ToolResult:
    """Ergebnis eines Werkzeugaufrufs."""

    ok: bool
    summary: str
    data: dict[str, Any] = field(default_factory=dict)
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "summary": self.summary, "data": self.data, "executed": self.executed}


@dataclass(frozen=True)
class Tool:
    """Ein aufrufbares Werkzeug."""

    name: str
    description: str
    params: dict[str, str]  # param_name -> kurze Beschreibung
    handler: Callable[[dict[str, Any], "ToolContext"], ToolResult]


@dataclass
class ToolContext:
    """Laufzeit-Kontext: Arbeitsbereich + Ausfuehrungsmodus + optionaler Shopify-Client."""

    workspace: Path
    execute: bool = False
    shopify: ShopifyClient | None = None

    def shopify_client(self) -> ShopifyClient:
        return self.shopify if self.shopify is not None else ShopifyClient()

    def safe_path(self, candidate: str) -> Path:
        result = validate_path_within_root(self.workspace, candidate)
        if not result.allowed or result.resolved is None:
            raise ValueError(f"unsicherer Pfad abgelehnt: {result.reason}")
        return result.resolved


# --------------------------------------------------------------------------- #
# Werkzeug-Handler
# --------------------------------------------------------------------------- #
def _tool_web_suche(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    query = str(args.get("query") or args.get("suche") or "").strip()
    if not query:
        return ToolResult(False, "Kein Suchbegriff angegeben.")
    url = build_google_search_url(query)
    return ToolResult(True, f"Suche vorbereitet: {query}", {"url": url, "query": query})


def _tool_webseite(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    raw = str(args.get("url") or "").strip()
    url = normalize_web_url(raw)
    if url is None:
        return ToolResult(False, f"Unsichere oder ungueltige URL abgelehnt: {raw!r}")
    return ToolResult(True, f"Webseite bereit zum Oeffnen: {url}", {"action": "open_website", "params": {"url": url}})


def _tool_app_starten(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    app = str(args.get("app") or args.get("name") or "").strip()
    if not app:
        return ToolResult(False, "Kein App-Name angegeben.")
    return ToolResult(True, f"App-Start vorbereitet: {app}", {"action": "open_app", "params": {"app": app}})


def _tool_datei_schreiben(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    rel = str(args.get("path") or args.get("pfad") or "").strip()
    content = str(args.get("content") or args.get("inhalt") or "")
    if not rel:
        return ToolResult(False, "Kein Dateipfad angegeben.")
    try:
        target = ctx.safe_path(rel)
    except ValueError as exc:
        return ToolResult(False, str(exc))
    if not ctx.execute:
        return ToolResult(True, f"Wuerde Datei schreiben: {rel} ({len(content)} Zeichen)", {"path": str(target), "bytes": len(content.encode('utf-8'))})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return ToolResult(True, f"Datei geschrieben: {rel} ({len(content)} Zeichen)", {"path": str(target), "bytes": len(content.encode('utf-8'))}, executed=True)


def _tool_datei_lesen(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    rel = str(args.get("path") or args.get("pfad") or "").strip()
    if not rel:
        return ToolResult(False, "Kein Dateipfad angegeben.")
    try:
        target = ctx.safe_path(rel)
    except ValueError as exc:
        return ToolResult(False, str(exc))
    if not target.exists():
        return ToolResult(False, f"Datei nicht gefunden: {rel}")
    text = target.read_text(encoding="utf-8")
    return ToolResult(True, f"Datei gelesen: {rel} ({len(text)} Zeichen)", {"path": str(target), "content": text})


def _tool_notiz(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    note = str(args.get("note") or args.get("text") or "").strip()
    if not note:
        return ToolResult(False, "Keine Notiz angegeben.")
    if not ctx.execute:
        return ToolResult(True, f"Wuerde Notiz ablegen: {note[:60]}", {"note": note})
    target = ctx.safe_path("notizen.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(f"- {note}\n")
    return ToolResult(True, f"Notiz gespeichert: {note[:60]}", {"note": note, "path": str(target)}, executed=True)


def _tool_shop_bauen(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    blueprint = build_shop_blueprint(
        name=str(args.get("name") or args.get("shop") or "Mein Shop"),
        sells=str(args.get("sells") or args.get("produkt") or args.get("was") or ""),
        audience=str(args.get("audience") or args.get("zielgruppe") or args.get("fuer_wen") or ""),
        style=str(args.get("style") or args.get("stil") or ""),
        product_count=int(args.get("product_count") or args.get("anzahl") or 8),
    )
    slug = blueprint["slug"]
    md = blueprint["markdown"]
    data = {"slug": slug, "products": len(blueprint["products"]), "collections": len(blueprint["collections"])}
    if not ctx.execute:
        return ToolResult(True, f"Wuerde Shop-Bauplan '{blueprint['name']}' mit {data['products']} Produkten erzeugen.", data)
    base = ctx.safe_path(f"shops/{slug}")
    base.mkdir(parents=True, exist_ok=True)
    (base / "shop_plan.md").write_text(md, encoding="utf-8")
    (base / "shop_plan.json").write_text(json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8")
    data["path"] = str(base)
    return ToolResult(True, f"Shop-Bauplan '{blueprint['name']}' erstellt: {data['products']} Produkte, {data['collections']} Kollektionen.", data, executed=True)


def _tool_shop_veroeffentlichen(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    """Baut den Bauplan und legt den Shop live in Shopify an (Produkte als Entwurf)."""

    blueprint = build_shop_blueprint(
        name=str(args.get("name") or args.get("shop") or "Mein Shop"),
        sells=str(args.get("sells") or args.get("produkt") or args.get("was") or ""),
        audience=str(args.get("audience") or args.get("zielgruppe") or ""),
        style=str(args.get("style") or args.get("stil") or ""),
        product_count=int(args.get("product_count") or args.get("anzahl") or 8),
    )
    client = ctx.shopify_client()
    data = {
        "slug": blueprint["slug"],
        "planned_products": len(blueprint["products"]),
        "planned_collections": len(blueprint["collections"]),
        "shopify_ready": client.available(),
    }
    if not client.available():
        return ToolResult(
            False,
            "Shopify-Zugangsdaten fehlen. Setze SHOPIFY_STORE und SHOPIFY_ADMIN_TOKEN, "
            f"dann lege ich '{blueprint['name']}' ({data['planned_products']} Produkte) live an. "
            "Bis dahin nutze 'shop_bauen' fuer den Bauplan.",
            data,
        )
    if not ctx.execute:
        return ToolResult(
            True,
            f"Wuerde '{blueprint['name']}' live in Shopify anlegen: "
            f"{data['planned_products']} Produkte, {data['planned_collections']} Kollektionen.",
            data,
        )
    result = publish_blueprint(blueprint, client)
    data.update(result.to_dict())
    return ToolResult(result.ok, result.summary, data, executed=result.ok)


def _tool_shop_info(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    client = ctx.shopify_client()
    if not client.available():
        return ToolResult(False, "Shopify-Zugangsdaten fehlen (SHOPIFY_STORE + SHOPIFY_ADMIN_TOKEN).", {"shopify_ready": False})
    try:
        shop = client.get_shop()
    except Exception as exc:
        return ToolResult(False, f"Shop-Info nicht abrufbar: {exc}")
    info = {k: shop.get(k) for k in ("name", "domain", "email", "currency", "plan_name", "country_name") if k in shop}
    return ToolResult(True, f"Store: {shop.get('name', '?')} ({shop.get('domain', '?')})", {"shop": info}, executed=True)


def _tool_shop_produkte(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    client = ctx.shopify_client()
    if not client.available():
        return ToolResult(False, "Shopify-Zugangsdaten fehlen.", {"shopify_ready": False})
    try:
        products = client.search_products(query=str(args.get("query") or ""), first=int(args.get("first") or 10))
    except Exception as exc:
        return ToolResult(False, f"Produkte nicht abrufbar: {exc}")
    names = [p.get("title") for p in products]
    return ToolResult(True, f"{len(products)} Produkte gefunden.", {"products": names}, executed=True)


def _tool_shop_bestellungen(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    client = ctx.shopify_client()
    if not client.available():
        return ToolResult(False, "Shopify-Zugangsdaten fehlen.", {"shopify_ready": False})
    try:
        orders = client.list_orders(first=int(args.get("first") or 10))
    except Exception as exc:
        return ToolResult(False, f"Bestellungen nicht abrufbar: {exc}")
    return ToolResult(True, f"{len(orders)} Bestellungen abgerufen.", {"orders": len(orders)}, executed=True)


def _tool_shop_rabatt(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    code = str(args.get("code") or "").strip().upper()
    percentage = args.get("percentage") or args.get("prozent") or 10
    if not code:
        return ToolResult(False, "Kein Rabattcode angegeben (z. B. code=SOMMER10).")
    client = ctx.shopify_client()
    if not client.available():
        return ToolResult(False, "Shopify-Zugangsdaten fehlen (SHOPIFY_STORE + SHOPIFY_ADMIN_TOKEN).", {"shopify_ready": False})
    data = {"code": code, "percentage": float(percentage)}
    if not ctx.execute:
        return ToolResult(True, f"Wuerde Rabattcode '{code}' ({percentage}%) anlegen.", data)
    try:
        created = client.create_discount(code=code, percentage=float(percentage))
    except Exception as exc:
        return ToolResult(False, f"Rabatt nicht angelegt: {exc}", data)
    data["discount_code_id"] = created.get("discount_code", {}).get("id")
    return ToolResult(True, f"Rabattcode '{code}' ({percentage}%) angelegt.", data, executed=True)


def _tool_plugins(args: dict[str, Any], ctx: ToolContext) -> ToolResult:
    from open_jarvis.enterprise import catalog

    plugins = catalog.all_plugins()
    query = str(args.get("query") or "").strip().lower()
    if query:
        plugins = [p for p in plugins if query in p.lower()]
    return ToolResult(True, f"{len(plugins)} Plugins gefunden.", {"plugins": plugins[:50], "total": len(plugins)})


def build_default_registry() -> dict[str, Tool]:
    """Standard-Werkzeuge des JARVIS-Agenten."""

    tools = [
        Tool("web_suche", "Bereitet eine sichere Websuche (Google) vor.", {"query": "Suchbegriff"}, _tool_web_suche),
        Tool("webseite", "Oeffnet eine Webseite nach Sicherheitspruefung.", {"url": "Adresse der Seite"}, _tool_webseite),
        Tool("app_starten", "Startet eine Desktop-Anwendung.", {"app": "Name der App"}, _tool_app_starten),
        Tool("datei_schreiben", "Schreibt eine Datei im Arbeitsbereich.", {"path": "relativer Pfad", "content": "Inhalt"}, _tool_datei_schreiben),
        Tool("datei_lesen", "Liest eine Datei aus dem Arbeitsbereich.", {"path": "relativer Pfad"}, _tool_datei_lesen),
        Tool("notiz", "Legt eine Notiz/Erinnerung ab.", {"note": "Notiztext"}, _tool_notiz),
        Tool("shop_bauen", "Erzeugt einen kompletten, verkaufsfertigen Shop-Bauplan.", {"name": "Shop-Name", "sells": "was verkauft wird", "audience": "Zielgruppe", "style": "Stil"}, _tool_shop_bauen),
        Tool("shop_veroeffentlichen", "Legt den Shop live in Shopify an (Produkte als Entwurf). Braucht SHOPIFY_STORE + SHOPIFY_ADMIN_TOKEN.", {"name": "Shop-Name", "sells": "was verkauft wird", "audience": "Zielgruppe", "style": "Stil"}, _tool_shop_veroeffentlichen),
        Tool("shop_info", "Zeigt Infos zum verbundenen Shopify-Store (Name, Domain, Waehrung).", {}, _tool_shop_info),
        Tool("shop_produkte", "Sucht/listet Produkte im Shopify-Store.", {"query": "optionaler Suchbegriff", "first": "Anzahl"}, _tool_shop_produkte),
        Tool("shop_bestellungen", "Ruft die letzten Bestellungen aus Shopify ab.", {"first": "Anzahl"}, _tool_shop_bestellungen),
        Tool("shop_rabatt", "Legt einen Prozent-Rabattcode in Shopify an.", {"code": "Rabattcode", "percentage": "Prozent"}, _tool_shop_rabatt),
        Tool("plugins", "Listet verfuegbare JARVIS-Plugins auf.", {"query": "optionaler Filter"}, _tool_plugins),
    ]
    return {tool.name: tool for tool in tools}


def describe_tools(registry: dict[str, Tool]) -> str:
    """Kompakte Werkzeugbeschreibung fuer den Planer-Prompt."""

    lines = []
    for tool in registry.values():
        params = ", ".join(f"{name} ({desc})" for name, desc in tool.params.items()) or "keine"
        lines.append(f"- {tool.name}: {tool.description} Parameter: {params}")
    return "\n".join(lines)
