# JARVIS ↔ Shopify — Faehigkeiten (aus dem Shopify-MCP gespiegelt)

JARVIS ist über den `ShopifyClient` (`open_jarvis/agent/shopify_client.py`) an die
**Shopify-Admin-API** angebunden und spiegelt den Funktionsumfang des Shopify-MCP-
Werkzeugsatzes. Der verbundene Test-Store dieses Projekts: **My Store**
(`www.katzenufos.com`, Währung CHF, Schweiz).

## Zugang einrichten

```bash
export SHOPIFY_STORE="mein-shop"          # oder mein-shop.myshopify.com
export SHOPIFY_ADMIN_TOKEN="shpat_..."     # Admin-API-Zugriffstoken
```

Ohne diese zwei Variablen meldet jede Methode klar „Zugangsdaten fehlen" und
JARVIS bleibt im Bauplan-Modus (`shop_bauen`).

## Zuordnung: Shopify-MCP-Werkzeug → JARVIS

| Shopify-MCP-Werkzeug | JARVIS-Methode | Zweck |
|---|---|---|
| `get-shop-info` | `ShopifyClient.get_shop` | Store-Infos (Name, Domain, Waehrung, Plan) |
| `search_products` | `ShopifyClient.search_products` | Produkte suchen/auflisten |
| `get-product` | `ShopifyClient.get_product` | Ein Produkt per ID abrufen |
| `create-product` | `ShopifyClient.create_product` | Produkt anlegen (Standard: Entwurf) |
| `update-product` | `ShopifyClient.update_product` | Produkt aendern (Titel, Text, Status) |
| `bulk-update-product-status` | `ShopifyClient.bulk_update_product_status` | Status mehrerer Produkte setzen |
| `search_collections` | `ShopifyClient.search_collections` | Kollektionen auflisten |
| `get-collection` | `ShopifyClient.get_collection` | Eine Kollektion abrufen |
| `create-collection` | `ShopifyClient.create_collection` | Kollektion anlegen |
| `update-collection` | `ShopifyClient.update_collection` | Kollektion aendern |
| `add-to-collection` | `ShopifyClient.add_to_collection` | Produkte einer Kollektion hinzufuegen |
| `list-orders` | `ShopifyClient.list_orders` | Bestellungen auflisten |
| `get-order` | `ShopifyClient.get_order` | Eine Bestellung abrufen |
| `list-customers` | `ShopifyClient.list_customers` | Kunden auflisten/suchen |
| `get-inventory-levels` | `ShopifyClient.get_inventory_levels` | Lagerbestaende abrufen |
| `set-inventory` | `ShopifyClient.set_inventory` | Lagerbestand setzen |
| `create-discount` | `ShopifyClient.create_discount` | Prozent-Rabattcode anlegen |
| `run-analytics-query` | `ShopifyClient.run_analytics_query` | ShopifyQL-Analytics (Umsatz, Sessions ...) |
| `graphql_query` | `ShopifyClient.graphql` | beliebige Admin-GraphQL-Abfrage |
| `graphql_mutation` | `ShopifyClient.graphql` | beliebige Admin-GraphQL-Mutation |
| `get-new-store-previews` | (nur ueber Shopify-MCP / claude.ai) | Neuen Store mit Design-Vorschauen generieren |
| `switch-shop` | (Store via SHOPIFY_STORE waehlen) | Store wechseln |
| `graphql_schema` | (Entwickler-Hilfe im MCP) | GraphQL-Schema erkunden |
| `validate_graphql_codeblocks` | (Entwickler-Hilfe im MCP) | GraphQL vor Ausfuehrung pruefen |
| `search_docs_chunks` | (Entwickler-Hilfe im MCP) | Shopify-Doku durchsuchen |

> Hinweis: `get-new-store-previews`, `switch-shop` und die GraphQL-Entwickler-
> Hilfen sind interaktive MCP-Funktionen (claude.ai). In JARVIS deckt der
> generische `ShopifyClient.graphql(query, variables)` beliebige Admin-GraphQL-
> Operationen ab; einen Store wählst du über `SHOPIFY_STORE`.

## Agent-Werkzeuge (per Sprachbefehl)

Der JARVIS-Agent nutzt diese Shopify-Fähigkeiten über Werkzeuge:

| Werkzeug | Beispiel-Befehl |
|---|---|
| `shop_veroeffentlichen` | „stelle einen Shop für Kaffee namens Bergbohne live auf Shopify online" |
| `shop_info` | „welcher Shop ist verbunden — Store-Info" |
| `shop_produkte` | „zeig mir meine Produkte im Shop" |
| `shop_bestellungen` | „zeig mir meine Bestellungen" |
| `shop_rabatt` | „lege einen Rabattcode SOMMER20 mit 20% an" |

Schreibende Werkzeuge (`shop_rabatt`, `shop_veroeffentlichen`) laufen ohne
`--execute` als **Vorschau** und rufen die Shopify-API nicht auf.

## Programmatisch

```python
from open_jarvis.agent.shopify_client import ShopifyClient

client = ShopifyClient()  # liest SHOPIFY_STORE + SHOPIFY_ADMIN_TOKEN aus der Umgebung
if client.available():
    print(client.get_shop()["name"])
    client.create_discount(code="SOMMER20", percentage=20)
    data = client.run_analytics_query("FROM sales SHOW total_sales SINCE -30d UNTIL today")
    result = client.graphql("query { shop { name } }")  # beliebige Admin-GraphQL
```

Alle schreibenden Aktionen legen Produkte als **Entwurf** (`draft`) an — nichts
wird versehentlich sofort öffentlich verkauft.
