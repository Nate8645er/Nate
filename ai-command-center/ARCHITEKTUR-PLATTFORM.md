# AI Command Center – Plattform-Architektur & Roadmap

Dieses Dokument ordnet die Enterprise-Vision (universelle Multi-Agent-KI-Plattform
für jede Branche) ehrlich ein: **Was ist heute gebaut und läuft**, was ist **teilweise**
da, und was ist **Roadmap**. Keine Behauptungen – der Code ist die Wahrheit.

## Technologie-Stack (und warum)

| Schicht | Wahl | Begründung |
|---|---|---|
| App/Frontend | **Next.js (App Router) + TypeScript + Tailwind** | Ein Framework für UI + API-Routen, server-side sicher, schnell deploybar (Vercel). |
| Agenten-Laufzeit | **Eigener Orchestrator** (`lib/agents/`) | Provider-agnostisch, streamend, plan-gesteuert – kein schwergewichtiges Framework nötig. |
| KI-Modelle | **Anthropic Claude, OpenAI, Moonshot** mit Fallback-Kette | Ausfallsicherheit: fällt ein Anbieter aus, übernimmt der nächste. Lokale Modelle nachrüstbar (Adapter-Muster). |
| Web-Recherche | **Eingebauter Browser** (DuckDuckGo→Bing→Wikipedia) | Aktuelle Fakten mit Quellen, ohne teuren Such-API-Key; SSRF-geschützt. |
| Lizenz/Abrechnung | **HMAC-signierte Tokens** + Shopify-Webhook | Stateless, manipulationssicher, kein Backend-Zwang. |
| Persistenz (Client) | **localStorage** | Arbeitsdaten bleiben beim Nutzer (Datenschutz), kein Fremd-Server. |

## Was HEUTE läuft (✅ gebaut & getestet)

- **Multi-Agent-Orchestrator**: Commander (CEO) → Worker-Agenten → Quality-Gate mit
  Score. Plan-abhängiger Fan-out (`WORKERS_BY_PLAN`).
- **Org-Modus** (BUSINESS/ENTERPRISE): Der Commander gründet pro Mission eine
  **virtuelle Firma** aus Abteilungen und Spezialisten und kann **dynamisch neue
  Agenten** erzeugen.
- **Benanntes Agenten-Roster (37 Spezialisten, 9 Abteilungen)** – `lib/agents/roster.ts`,
  Übersicht unter `/agenten`. Der Org-Planer besetzt Rollen bevorzugt aus diesem Pool.
- **KI-Chat wie ChatGPT/Claude** mit **eingebautem Browser + Quellen**, gestreamt.
- **Missionen → fertige Dateien** (Website/Dokument/Code) mit Download.
- **79 Skills** über 12 Kategorien für praktisch jede Branche.
- **E-Mail-Zentrale** (LLM-Entwurf → Gmail/WhatsApp vorausgefüllt), **Kunden-CRM**,
  **Autopilot** (wiederkehrende Aufträge), **Berichte**, **Analysen**.
- **Sicherheit**: signierte Lizenzen, Prompt-Injection-Schutz (Web/Dokumente als
  Daten), SSRF-Schutz im Browser, verschlüsselte Übertragung, Provider-Fallback.
- **Dokumenten-Analyse** (`/api/extract`): PDF/Text einlesen und verarbeiten.
- **Verschiedene KI-Modelle, lokal UND Cloud**: Provider-Schicht unterstützt
  Anthropic, OpenAI, Moonshot **und einen lokalen/eigenen, OpenAI-kompatiblen
  Provider** (`local`, z. B. Ollama/vLLM/LM Studio) – aktiv, sobald
  `LOCAL_LLM_URL` gesetzt ist. Fallback-Kette überspringt nicht konfigurierte
  Provider automatisch.

## Teilweise vorhanden (🟡)

- **Firmen-Integrationen** (SAP, Salesforce, HubSpot, Slack, Dropbox, eigene REST-API):
  als **Katalog** vorhanden, live-Anbindung pro Firma als Projekt (`lib/connectors.ts`).
- **Bild-/Video-/Sprach-Agenten**: als Rollen im Roster definiert; die **multimodale
  Laufzeit** (Vision-Eingabe, Sprache-zu-Text) ist der nächste Ausbauschritt.
- **RAG/Wissensspeicher**: Firmenkontext (Branche/Kunden/Signatur) fliesst heute in
  jede Mission; echte Vektor-DB + Wissensgraph sind Roadmap.

## Roadmap (🗺️ bewusst noch nicht gebaut – ehrlich)

Diese Enterprise-Bausteine sind sinnvoll, aber sie gehören in eine dedizierte
Backend-Plattform und werden **nicht** vorgetäuscht:

- Microservices, Message-Queue, Event-Bus
- Vektordatenbank + Wissensgraph + echtes RAG-Retrieval
- GraphQL-API zusätzlich zu den bestehenden REST-Routen
- Mandantenfähigkeit auf Server-Ebene, rollenbasierte Rechte serverseitig
- Docker/Kubernetes-Deployment, Hochverfügbarkeit, zentrales Logging/Monitoring

**Empfohlene nächste Schritte (in dieser Reihenfolge):**
1. Multimodal: Bild-Analyse (Vision) + Sprach-Eingabe im Chat.
2. Datei-Upload im Chat (PDF/Excel/CSV) → Analyse durch den Dokumenten-Agenten.
3. Echtes Gmail/Kalender via OAuth (ein Connector live schalten).
4. Persistenz-Backend + Vektor-DB für echtes Langzeit-Firmenwissen (RAG).

---
Stand: laufend. Jede Zeile unter „läuft" ist im Code vorhanden und baut grün
(`next build`). Erweiterungen kommen schrittweise, getestet, ohne Platzhalter.
