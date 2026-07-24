# BESTAND.md — Phase 0: Bestandsaufnahme

> Erstellt: 2026-07-24 · Branch: `claude/ai-team-fable-5-boss-6iim48`
> Modus: FABLE-5-MAX (ULTRA AI ENTERPRISE OS als virtuelles Team)
> Regel dieser Phase: **kein Code, nichts gelöscht, nichts verändert.** Reine Inventur.

Diese Datei bewertet den Ist-Zustand des Repos gegen den Master-Prompt
(Produkt A = KI-Plattform, B = Shopify-Abo-Store, C = Creative-Pipeline).
Legende: **[V]** vorhanden · **[W]** wiederverwendbar · **[F]** fehlt.

---

## 1. Was im Repo liegt (Ist-Zustand)

| Pfad | Inhalt | Status |
|------|--------|--------|
| `ultra-enterprise-os/` | Claude-Code-Plugin: Meta-Orchestrator „ULTRA AI ENTERPRISE OS" | **[V][W]** |
| `ultra-enterprise-os/skills/ultra-enterprise-os/` | `SKILL.md` (Betriebsprotokoll) + `references/org-chart.md` | **[V][W]** |
| `ultra-enterprise-os/agents/` | 10 Rollen-Agenten (architect, business, data-ml, design, devops, docs, fullstack, orchestrator, qa, security) | **[V][W]** |
| `ultra-enterprise-os/commands/` | 3 Slash-Commands: `ultra`, `ultra-team`, `ultra-review` | **[V][W]** |
| `.claude/` | Aktive Installation: **exaktes Spiegelbild** von `ultra-enterprise-os/` (agents/commands/skills identisch, per `diff` bestätigt) | **[V]** |
| `.claude/settings.json` | Registriert `nate-marketplace` (github: `Nate8645er/Nate`), aktiviert Plugin `ultra-enterprise-os` | **[V]** |
| `.claude-plugin/marketplace.json` | Privater Marketplace „nate-marketplace" mit einem Plugin | **[V]** |
| `javier-mobile/` | Lauffähige JARVIS-PWA fürs iPhone: FastAPI + Anthropic Tool-Use-Agent | **[V][W]** |
| `javier-mobile/server.py` (249 Z.) | FastAPI-Server + Tool-Use-Loop (nutzt Modell `claude-sonnet-4-6`) | **[V][W]** |
| `javier-mobile/tools.py` (697 Z.) | Agent-Tools: Todos, Kalender, Wetter, **Shopify read-only**, Nachrichten, PC-Aktionen | **[V][W]** |
| `javier-mobile/instagram.py` (82 Z.) | Optionales Instagram-Graph-API-Modul | **[V][W]** |
| `javier-mobile/static/` | PWA-Frontend: `index.html`, `manifest.json`, `sw.js`, Icons | **[V]** |
| `javier-mobile/.env.example` + `.gitignore` | Saubere Secret-Vorlage; `.env` wird ignoriert | **[V]** |
| `render.yaml` | Ein-Klick-Deploy von `javier-mobile` auf Render (Free-Tier) | **[V]** |
| `.github/workflows/platform-backend-release.yml` | CI: baut Docker-Image `platform-backend` → GHCR (Tag `pb-v*` / manuell) | **[V]** ⚠️ |

---

## 2. Angebundene MCP-Server & Werkzeuge (Session-Ebene)

Bereits **verbunden** und nutzbar — deckt große Teile von B und C ab, **ohne Neuinstallation**:

| MCP-Server | Deckt ab | Relevanz |
|------------|----------|----------|
| **Shopify** (offiziell) | Produkte, Collections, Orders, Kunden, Inventar, GraphQL, ShopifyQL, Docs, Store-Previews | **Produkt B** (Store-Aufbau + Betrieb) |
| **Higgsfield** | Bild-, Video-, Audio-/TTS-Generierung, Voice-Cloning, Explainer-Videos, Upscale, BG-Removal, TikTok-Publishing, Virality-Predictor | **Produkt C** (Creative-Pipeline) |
| **Meta_System** | Meta Ads: Kampagnen, Ad-Sets, Creatives, Catalog, Pixel, Audiences, Insights | Marketing für B/C |
| **github** | Repos, PRs, Issues, Actions, Code-Suche, Secret-Scanning | Betrieb/CI |
| **Gmail**, **Google_Drive** | Mail-Flows, Datei-Ablage | Onboarding/Support |

**Noch nicht angebunden** (laut Master-Prompt Kap. 2/3 bei Bedarf pro Phase): LiteLLM-Gateway, Stripe/Lago (Billing), ElevenLabs, context7, Playwright, Supabase, Remotion. → **[F]**, bewusst erst wenn die jeweilige Phase sie braucht (Master-Prompt Regel 1: „kein Blind-Installieren").

---

## 3. Abgleich mit den drei Produkten des Master-Prompts

### Produkt A — KI-Plattform (Multi-Tenant SaaS)  → **[F] fehlt fast vollständig**
- Kein Anwendungscode vorhanden (kein Backend, keine DB, keine Auth, kein LiteLLM-Gateway, keine Tarif-/Mandantenlogik, kein Widget-Dashboard).
- **Einziges Fragment:** die CI `platform-backend-release.yml` erwartet einen Ordner `platform-backend/` — **dieser existiert nicht** (siehe Risiko R1).
- **Wiederverwendbar aus dem Bestand:** das Tool-Use-Agent-Muster aus `javier-mobile/server.py` (Anthropic-Loop) und die Shopify-Read-Integration aus `tools.py` sind gute Vorlagen für die Agenten-Ebene von A.

### Produkt B — Shopify-Abo-Store  → **[F] fehlt (Code), [V] Werkzeug bereit**
- Kein Theme, keine Tarif-Seite, kein Checkout, keine Webhooks, keine CH-Rechtstexte im Repo.
- **Aber:** Shopify-MCP ist verbunden → Store-Aufbau kann direkt starten (Master-Prompt Kap. 4).

### Produkt C — Creative-/Video-/Stimmen-Pipeline  → **[F] fehlt (Code), [V] Werkzeug bereit**
- Keine Remotion-Templates, keine Asset-Ablage, kein Render-Skript im Repo.
- **Aber:** Higgsfield-MCP deckt Bild/Video/TTS/Voice/Explainer bereits ab → Produktion kann ohne lokale GPU starten. ElevenLabs (Master-Prompt Kap. 5.4) optional später.

---

## 4. Duplikate & Redundanzen (identifiziert, NICHT entfernt)

1. **`ultra-enterprise-os/{agents,commands,skills}` ↔ `.claude/{agents,commands,skills}`** — byte-identisch (per `diff -rq` verifiziert). Das ist **kein Fehler**, sondern das erwartete Verhältnis „Plugin-Quelle ↔ aktive Installation". **Risiko:** Drift, wenn künftig nur eine Seite editiert wird. **Empfehlung:** immer die Plugin-Quelle (`ultra-enterprise-os/`) editieren, `.claude/` als generierten Stand behandeln. (Keine Aktion in Phase 0.)

---

## 5. Risiken (ehrlich benannt)

| # | Risiko | Schwere | Empfehlung |
|---|--------|---------|------------|
| **R1** | CI `platform-backend-release.yml` referenziert `context: platform-backend`, Ordner fehlt → Workflow schlägt bei Auslösung fehl | mittel | In Phase 2 (Fundament A) den Ordner anlegen ODER die CI bis dahin nur manuell/getaggt lassen. Nicht löschen — sie ist das Release-Gerüst für A. |
| **R2** | Kein Root-`.gitignore`. Nur `javier-mobile/.gitignore` schützt dessen `.env`. Neue Produkte (A/B/C) legen eigene `.env` an → Secret-Leak-Gefahr | hoch (präventiv) | In Phase 1 einen Root-`.gitignore` ergänzen (additiv), bevor A/B/C-Code entsteht. |
| **R3** | `javier-mobile` nutzt `claude-sonnet-4-6` (älteres Modell) | niedrig | Kein Handlungsdruck; bei Ausbau auf aktuelles Modell heben. Bestandscode bleibt unverändert (Master-Prompt-Regel: additiv). |
| **R4** | Master-Prompt-Katalog listet ~60 Repos/MCP — Versuchung zum Über-Installieren | mittel | Master-Prompt Regel 1 befolgen: pro Phase nur das Nötige. |

---

## 6. Fazit & nächster Schritt

**Vorhanden & stark:** ein sauberes Orchestrierungs-Fundament (ULTRA-Plugin + 10 Agenten) und eine lauffähige Referenz-App (`javier-mobile`) mit gutem Tool-Use- und Shopify-Muster. **Verbundene MCP-Server** decken B und C werkzeugseitig schon ab.

**Vorhanden & schwach / fehlend:** die drei eigentlichen Produkte A/B/C existieren als Code noch nicht — A ist nur als CI-Gerüst angedeutet (und dort inkonsistent, R1).

**Nichts wurde gelöscht oder verändert.** Diese Datei ist reine Inventur.

**Nächster konkreter Schritt → Phase 1 (Werkzeuge & Absicherung):**
1. Root-`.gitignore` additiv anlegen (R2 schließen), bevor irgendein A/B/C-Code entsteht.
2. Basis-MCP-Bedarf gegen bereits Verbundenes abgleichen und `MCP-STATUS.md` schreiben (nur wirklich fehlende Server nennen, nicht blind installieren).
3. Entscheidung zu R1 (platform-backend-CI) mit Nate abstimmen, sobald Phase 2 startet.
