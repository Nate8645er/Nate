# MCP-STATUS.md — Phase 1: Werkzeug-Abgleich

> Erstellt: 2026-07-24 · Branch: `claude/ai-team-fable-5-boss-6iim48`
> Prinzip (Master-Prompt Kap. 1, Regel 1): **Katalog ≠ Einkaufsliste.**
> Pro Phase nur installieren, was die Phase braucht. Hier: Ist-Stand ehrlich
> dokumentiert, nicht blind erweitert.

---

## 1. Wichtige Klarstellung zum Betrieb

Diese Sitzung läuft in einer **verwalteten Remote-Umgebung** (Claude Code on the web).
MCP-Server werden hier **auf Session-Ebene bereitgestellt**, nicht durch persistente
`claude mcp add …`-Einträge auf einem lokalen Rechner. Die `claude mcp add`-Befehle
aus dem Master-Prompt (Kap. 2.2 ff.) gehören in die **lokale** Claude-Code-Konfiguration
auf Nates Rechner und persistieren dort — in dieser Cloud-Session haben sie keinen
dauerhaften Effekt. Deshalb unten zwei Spalten: „Session (jetzt verbunden)" und
„Lokal einzurichten (Master-Prompt)".

---

## 2. Jetzt in dieser Session verbunden & getestet

| MCP-Server | Getestet via | Ergebnis | Deckt Produkt ab |
|------------|--------------|----------|------------------|
| **github** | `list_pull_requests`, `create_pull_request` (PR #45) | ✅ funktioniert | Betrieb/CI (alle) |
| **Shopify** | Toolschema geladen (search/create/orders/graphql/ShopifyQL) | ✅ verbunden | **Produkt B** |
| **Higgsfield** | Toolschema geladen (generate_image/video/audio, voice, explainer) | ✅ verbunden | **Produkt C** |
| **Meta_System** | Toolschema geladen (Ads/Catalog/Pixel/Insights) | ✅ verbunden | Marketing B/C |
| **Gmail** | Toolschema geladen (search/draft/label) | ✅ verbunden | Onboarding/Support |
| **Google_Drive** | Toolschema geladen (read/create/search) | ✅ verbunden | Asset-/Doku-Ablage |

> „Getestet" heißt hier: Server ist verbunden und Toolschema abrufbar; für github
> zusätzlich durch einen echten Aufruf (PR #45) verifiziert. Ehrlich: die anderen
> sind verbunden, aber noch nicht durch einen Schreibaufruf belastet — das passiert
> erst in der jeweiligen Produktphase mit vorheriger Kostenschätzung (Regel 5).

---

## 3. Master-Prompt-Basis (Kap. 2.2) — Soll-Abgleich

| Gewünscht (Kap. 2.2) | Zweck | Status hier |
|----------------------|-------|-------------|
| `server-github` | GitHub | ✅ als **github** verbunden |
| `context7` | aktuelle Lib-Doku | ⬜ lokal einzurichten (bei Bedarf in Bauphasen) |
| `playwright` | Browser-Automation | ⬜ Chromium + Playwright sind in der Umgebung vorinstalliert; MCP-Anbindung bei Bedarf |
| `chrome-devtools` | Perf/Netzwerk live | ⬜ erst bei Frontend-Härtung (Phase 7 / B-Lighthouse) |
| `filesystem` | Datei-Ops | ✅ native Datei-Tools der Session ersetzen das |
| `sequential-thinking` | Denk-Struktur | ⬜ optional; ULTRA-Orchestrierung deckt das methodisch ab |

**Fazit:** Von der Basis ist das Wesentliche (github, Datei-Zugriff) bereits abgedeckt.
`context7`, `playwright`, `chrome-devtools` werden **erst dann** ergänzt, wenn eine
konkrete Phase sie braucht — nicht auf Vorrat.

---

## 4. Produktspezifische Server — pro Phase, mit Kostenhinweis

| Server | Master-Prompt | Für Phase | Aktion |
|--------|---------------|-----------|--------|
| **LiteLLM** (Gateway) | Kap. 3.2 „Kern" | Phase 2 (Fundament A) | lokal/Container einrichten, sobald A startet |
| **Stripe** / **Lago** | Kap. 3.3 | Phase 4 (Billing) | erst bei Abrechnung; Stripe braucht Keys |
| **ElevenLabs** | Kap. 5.4 | Phase 6 (Creative, Finalton) | **kostenpflichtig** — erst Kokoro/Higgsfield lokal, ElevenLabs nur für Finalrender (Regel: Kap. 5.4) |
| **Shopify dev-mcp** | Kap. 4.1 | Phase 5 (Store B) | zusätzlich zum verbundenen Shopify-MCP für Liquid-Validierung |
| **Supabase** | Kap. 3.2 | Phase 2 | Multi-Tenant-DB + RLS |

**Kostenregel (Master-Prompt Regel 5):** Higgsfield/ElevenLabs/Veo/Suno laufen auf
Credits. Vor jedem generativen Batch nenne ich die geschätzten Kosten und generiere
erst nach Freigabe.

---

## 5. Sicherheitsnotiz (Regel 2 + 3)

- **Nur offizielle/erstrangige Quellen** in dieser Session verbunden (github, Shopify,
  Meta, Google) — keine kleinen Community-MCP ohne Prüfung installiert.
- Fremder MCP-Code läuft mit meinen Rechten → jede spätere Community-Ergänzung wird
  vorher geprüft (README, letzter Commit, Issues) und Nate kurz gemeldet.

---

## 6. Nächster Schritt

Phase 1 abgeschlossen (R2 geschlossen via Root-`.gitignore`, Werkzeugstand dokumentiert).
**Vor Phase 2** ist eine Entscheidung von Nate nötig (R1 + Grundsatz):

- **R1:** Soll die CI `platform-backend-release.yml` bestehen bleiben (Ordner
  `platform-backend/` wird in Phase 2 angelegt) oder bis dahin pausiert werden?
- **Scope Phase 2:** Fundament für Produkt A ist der größte Brocken (DB + RLS + Auth +
  LiteLLM + erster Chat). Bestätigung, dass ich hier mit dem Aufbau beginnen soll.
