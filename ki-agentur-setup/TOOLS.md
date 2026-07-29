# Werkzeug-Routing der KI-Agentur (Harmonisierung mit ULTRA Enterprise OS)

Dieses Dokument verbindet die installierten Tools mit dem **ULTRA Enterprise OS**
(Boss = `ultra-orchestrator`, Worker = die `ultra-*`-Agenten). Der Orchestrator
liest `tools-registry.json` und entscheidet **automatisch**, welches Werkzeug zu
einer Aufgabe passt — ohne Rueckfrage.

## Grundregel

> Wenn ein Tool die Aufgabe verbessert oder beschleunigt, wird es genutzt.
> Rueckfrage nur bei Admin-Rechten, API-Keys, Lizenzen oder Zwangseingaben.

## Aufgabe → Tool → verantwortlicher Agent

| Aufgabe | Tool | Owner-Agent (ULTRA) |
|---|---|---|
| KI-Bilder, Logos, Banner, Produktbilder, Werbegrafiken | **ComfyUI** | `ultra-design` |
| Bildgenerierung direkt aus dem Agenten heraus | **ComfyUI MCP** | `ultra-design` |
| ComfyUI automatisieren / Custom Nodes / Batch | **Comfy CLI** | `ultra-devops` |
| Webseiten automatisch testen/bedienen, E2E, Scraping | **browser-use** | `ultra-qa` |
| Multi-Agenten-Systeme, komplexe Workflows | **CrewAI** | `ultra-orchestrator` |
| Automatisierungen, Integrationen, Webhooks, E-Mail-Flows | **n8n** | `ultra-devops` |
| Dashboards, Datenanalyse, Reporting, BI, Kunden-KPIs | **Metabase** | `ultra-data-ml` |
| Verschiedene KI-Modelle nutzen, Routing, Kosten/Fallback | **OmniRoute** | `ultra-architect` |
| Schnelle Web-Prototypen, Landingpages, MVPs | **bolt.diy** | `ultra-fullstack` |

## Typische Agentur-Workflows (End-to-End)

**Unternehmenswebsite / Landingpage**
1. `ultra-fullstack` baut die Seite (Code direkt, oder **bolt.diy** fuer schnellen Prototyp)
2. `ultra-design` erzeugt Hero-/Produktbilder, Logo, OG-Image via **ComfyUI** (bzw. **ComfyUI MCP**)
3. `ultra-qa` testet die Seite automatisiert mit **browser-use**
4. `ultra-devops` haengt Formulare/Leads via **n8n** an (E-Mail, CRM)

**Onlineshop / Kundenportal**
1. Seite bauen (`ultra-fullstack`)
2. Produktbilder/Werbegrafiken (**ComfyUI**, `ultra-design`)
3. Bestell-/Automatisierungs-Flows (**n8n**, `ultra-devops`)
4. Umsatz-/Traffic-Dashboard (**Metabase**, `ultra-data-ml`)
5. E2E-Test des Checkouts (**browser-use**, `ultra-qa`)

**KI-Chatbot / komplexe Automatisierung**
- Multi-Agenten-Logik mit **CrewAI**, Modellzugriff gebuendelt ueber **OmniRoute**,
  Ausloeser/Anbindung ueber **n8n**.

## Dienste & Ports

| Tool | URL |
|---|---|
| ComfyUI | http://127.0.0.1:8188 |
| ComfyUI MCP | http://127.0.0.1:9000/mcp |
| n8n | http://127.0.0.1:5678 |
| Metabase | http://127.0.0.1:3000 |
| OmniRoute | http://127.0.0.1:20128 (API: `/v1`) |
| bolt.diy | http://localhost:5173 |

## Hinweis fuer den Boss (`ultra-orchestrator`)

Bei jeder eingehenden Aufgabe:
1. Aufgabentyp bestimmen → in `tools-registry.json` unter `aufgaben_routing` nachschlagen.
2. Passenden Owner-Agent aktivieren, Tool per Startskript hochfahren (falls Dienst).
3. Ergebnis durch `ultra-qa` (Funktion) und `ultra-security` (bei sicherheitsrelevanten Aenderungen) pruefen lassen.
