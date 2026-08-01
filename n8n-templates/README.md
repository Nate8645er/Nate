# n8n-Vorlagen-Sammlung (awesome-n8n-templates)

328 fertige n8n-Workflow-Vorlagen in 21 Kategorien, importbereit und validiert.
Quelle: [enescingoz/awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) (Lizenz CC-BY-4.0, siehe `LICENSE` und `UPSTREAM-README.md`).

## Inhalt

| Datei / Ordner | Zweck |
| --- | --- |
| `workflows/<Kategorie>/*.json` | Die Workflow-Vorlagen, je eine Datei pro Workflow |
| `catalog.json` | Maschinenlesbarer Index: Name, Kategorie, Node-Zahl, Trigger, Integrationen, benötigte Credentials |
| `INDEX.md` | Menschlich lesbarer Index, nach Kategorie gruppiert |
| `UPSTREAM-README.md` | Original-README der Quelle (Attribution) |

Alle JSONs sind geprüft: 7 Dateien hatten angehängten Textmüll nach dem JSON-Objekt und wurden repariert; die leere Datei `Other/ALL_unique_nodes.json` wurde weggelassen.

## Einen Workflow in n8n importieren

**Weg 1 – über die Oberfläche (empfohlen):**
1. In n8n oben rechts **Workflow erstellen** → Menü (⋯) → **Import from File**.
2. Die gewünschte `.json` aus `workflows/` auswählen – fertig.

**Weg 2 – per API (für viele auf einmal):**
```bash
# N8N_URL z. B. https://deine-instanz.app.n8n.cloud, API-Key unter Settings → n8n API
curl -X POST "$N8N_URL/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  --data @"workflows/Telegram/Telegram AI bot assistant_ ready made template for voice & text messages.json"
```

**Weg 3 – Copy-Paste:** JSON-Inhalt kopieren und in der n8n-Arbeitsfläche mit Ctrl+V einfügen.

## Nach dem Import (immer nötig)

1. **Credentials verbinden:** Jede Vorlage referenziert Zugangsdaten (siehe Spalte `credentials` in `catalog.json`). Diese werden **nicht** mitgeliefert – in n8n unter *Credentials* die eigenen Konten (OpenAI, Telegram, Google usw.) anlegen und in den Nodes auswählen.
2. **Platzhalter prüfen:** IDs von Sheets, Kanälen, Datenbanken usw. auf die eigenen Werte umstellen.
3. **Einmal manuell ausführen**, bevor der Workflow aktiviert wird.

## Vorlage finden

- Blättern: `INDEX.md`
- Suchen (Beispiel: alles mit Telegram + OpenAI):
```bash
python3 -c "
import json
for w in json.load(open('n8n-templates/catalog.json')):
    ints = ' '.join(w['integrations']).lower()
    if 'telegram' in ints and 'openai' in ints:
        print(w['name'], '->', w['file'])
"
```
