---
name: n8n-templates
description: >-
  Findet und liefert passende n8n-Workflow-Vorlagen aus der lokalen Sammlung
  n8n-templates/ (328 validierte Workflows in 21 Kategorien). Aktivieren wenn
  der User eine n8n-Automation sucht, bauen oder importieren will ("n8n
  Workflow fuer X", "Automation fuer Telegram/Gmail/Shopify", "gibt es eine
  Vorlage fuer ...", "importiere den Workflow"), oder wenn eine bestehende
  Vorlage angepasst werden soll.
---

# n8n-Vorlagen nutzen

Die Sammlung liegt im Repo unter `n8n-templates/`:

- `catalog.json` – Index aller Workflows mit `name`, `file`, `category`,
  `nodes`, `trigger`, `integrations`, `credentials`. **Immer zuerst hier
  suchen**, nie die 328 JSONs einzeln durchgehen.
- `workflows/<Kategorie>/<Name>.json` – die importierbare Vorlage.
- `INDEX.md` – menschenlesbarer Ueberblick, `README.md` – Import-Anleitung.

## Vorgehen

1. **Suchen:** `catalog.json` mit Python/jq nach Stichwort in `name`,
   `category` oder `integrations` filtern. Mehrere Treffer? Die 2–3 besten
   mit Name, Node-Zahl und benoetigten Credentials vorschlagen.
2. **Liefern:** Den Pfad zur JSON-Datei nennen und die Datei bei Bedarf per
   SendUserFile schicken (display: attach), damit der User sie in n8n
   importieren kann (Import from File oder Ctrl+V auf der Arbeitsflaeche).
3. **Ehrlich bleiben:** Credentials sind nie enthalten – immer sagen, welche
   Zugangsdaten der User in n8n selbst hinterlegen muss (steht im Katalog
   unter `credentials`). Platzhalter-IDs (Sheets, Kanaele) muss er anpassen.
4. **Anpassen:** Wird eine Variante gewuenscht, die JSON-Vorlage kopieren und
   gezielt Nodes/Parameter aendern – nie das Original ueberschreiben.
5. **API-Import:** Nur wenn der User eine n8n-Instanz + API-Key nennt:
   `POST $N8N_URL/api/v1/workflows` mit Header `X-N8N-API-KEY` und der JSON
   als Body. Keine Instanz-URL erfinden.
