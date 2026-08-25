# REPOSITORIES & MARKTPLAETZE

## Haupt-Repo
- **`Nate8645er/Nate`** — https://github.com/Nate8645er/Nate — oeffentlich.
  - Ist zugleich der Marktplatz **`nate-marketplace`** (`.claude-plugin/marketplace.json`).
  - Enthaelt: 6 Plugins, den wshobson-Marktplatz, curbcut, marketing, shop, n8n-templates, diesen `ai-business/`-Export.
  - Klonen liefert OpenCode den kompletten Werkzeugkasten.

## Im Repo vendored (mit Upstream-Herkunft)

| Ordner | Upstream / Autor | Zweck | Lizenz | Installationsweg |
|---|---|---|---|---|
| `../ultra-enterprise-os` | Nate (eigen) | ULTRA AI ENTERPRISE OS: Orchestrator + 12 Agenten | eigen | `/plugin install ultra-enterprise-os@nate-marketplace` |
| `../wshobson-agents` | **wshobson/agents** (github.com/wshobson/agents) | 91 Plugins, 202 Agents, 181 Skills, 105 Commands | siehe `wshobson-agents/LICENSE` | eigener Marktplatz-Baum; Agenten nach `.claude/agents/` kopieren |
| `../marketing-skillstack` | **coreyhaines31** | 49 Marketing-Skills | siehe Ordner | `/plugin install marketing-skillstack@nate-marketplace` |
| `../awesome-skillstack` | **Composio** (awesome-claude-skills) | 25 eigenstaendige Skills | siehe Ordner | `/plugin install awesome-skillstack@nate-marketplace` |
| `../design-skillstack` | Claude Design Skillstack | 22 Skills, 27 Agents (3D/Animation) | `design-skillstack/LICENSE` | `/plugin install design-skillstack@nate-marketplace` |
| `../threejs-skills` | **pinkforest** | 10 Three.js-Skills | siehe Ordner | `/plugin install threejs-skills@nate-marketplace` |
| `../security-guidance` | **David Dworken** (Anthropic) | Security-Hooks (Edit/Write/Stop/Commit) | `security-guidance/` | `/plugin install security-guidance@nate-marketplace` |
| `../n8n-templates` | Zie619 / n8n-workflows | 328 n8n-Automations-Workflows | `n8n-templates/LICENSE` | direkt in n8n importieren |

> Die genaue Herkunft/Lizenz steht jeweils in `README.md` / `LICENSE` / `PACKAGING-NOTES.md` des Ordners. Wo eine Lizenzdatei fehlt, ist der Upstream als Quelle genannt — vor Weitergabe pruefen.

## Eigene Produkt-/Arbeitsordner (im Repo)
- `../curbcut` — eigenes Barrierefreiheits-Produkt (Python).
- `../marketing` — eigene Ad-Assets (facebook, anzeigen, kurzfilme).
- `../shop` — Let'sDrink-Shopify-Arbeitsstand (Themes, Texte, Richtlinien, `werkzeuge/rat.py`).
- `../agenten-video`, `../javier-mobile`, `../setup` — weitere Arbeitsordner.

## Keine privaten Fremd-Repos kopiert
Es wurden nur Ordner dokumentiert/referenziert, die bereits im eigenen Repo liegen. Keine fremden privaten Repositories geklont oder kopiert.

## NOT FOUND
- Ausser `Nate8645er/Nate` hat das Konto keine weiteren zugaenglichen Repos (via `list_repos` geprueft).
- Ein separates `nate8645`-Konto (falls vorhanden) ist aus dieser Sitzung nicht erreichbar — die Git-Anmeldung gilt fuer `Nate8645er`.
