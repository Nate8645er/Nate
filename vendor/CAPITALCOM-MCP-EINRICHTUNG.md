# Capital.com MCP — Einrichtung

Zum Kopieren, wenn du am Rechner bist. **Auf dem Handy geht das nicht** —
`claude mcp add` braucht ein Terminal.

Geprüft am 06.09.2026: Paket `capitalcom-mcp` 0.3.4, Apache-2.0,
**unofficial** (nicht von Capital.com), Autor Simon Tarara,
github.com/SimonTarara62/capitalcom-mcp-server.
`uvx capitalcom-mcp --help` läuft sauber.

---

## 1. Befehl

**Windows / PowerShell**

```powershell
claude mcp add --transport stdio `
  --env CAP_ENV_FILE="$HOME\.config\capital-mcp\.env" `
  capitalcom -- uvx capitalcom-mcp==0.3.4
```

**macOS / Linux**

```bash
claude mcp add --transport stdio \
  --env CAP_ENV_FILE="$HOME/.config/capital-mcp/.env" \
  capitalcom -- uvx capitalcom-mcp==0.3.4
```

Die Version ist bewusst festgenagelt. Ohne `==0.3.4` zieht `uvx` immer
die neueste Fassung — bei einem Konto mit echtem Geld kann sich damit
über Nacht das Verhalten ändern.

## 2. Zugangsdaten

Interaktiv anlegen:

```bash
uvx capitalcom-mcp==0.3.4 init
uvx capitalcom-mcp==0.3.4 doctor
```

Oder von Hand als `~/.config/capital-mcp/.env`:

```
CAP_IDENTIFIER=deine@mail
CAP_API_KEY=...
CAP_API_PASSWORD=...

# Sicherheitsnetz fuer den Anfang - beides bewusst so:
CAP_DRY_RUN=true
CAP_ALLOW_TRADING=false
```

**Diese Werte gehören nirgendwo in einen Chat.** Wer einen
Passwortmanager nutzt, setzt stattdessen `CAP_API_KEY_CMD`,
`CAP_IDENTIFIER_CMD` und `CAP_API_PASSWORD_CMD` auf einen Befehl, der
das Geheimnis ausgibt — dann steht es nicht im Klartext auf der Platte.

## 3. Was das Ding darf

Rund 44 Werkzeuge: Konto, Märkte, Kurse, Streaming, Watchlists — **und
Handel**. Darunter `cap_trade_execute_position`,
`cap_trade_positions_close`, `cap_trade_orders_amend`,
`cap_trade_orders_cancel`. Das eröffnet und schliesst echte Positionen.

Das Sicherheitsmodell des Autors ist ordentlich gebaut:

- Handel ist **aus**, solange nicht `CAP_ALLOW_TRADING=true` **und** das
  Instrument in `CAP_ALLOWED_EPICS` steht
- Zwei-Stufen-Ausführung, Veränderungen brauchen `confirm=true`
- Limits für Grösse, offene Positionen und Orders pro Tag
- `CAP_DRY_RUN=true` blockt jede Ausführung

## 4. Reihenfolge, die ich empfehle

1. Demokonto bei Capital.com, nicht das echte
2. `CAP_DRY_RUN=true`, `CAP_ALLOW_TRADING=false`
3. Lesende Werkzeuge ausprobieren: Kurse, Konto, Watchlists
4. Erst wenn das erwartbar läuft: über mehr nachdenken — und dann mit
   enger `CAP_ALLOWED_EPICS`-Liste

## 5. Der Satz, der nicht in der Anleitung steht

Eine KI, die handeln darf, macht keine Gewinne planbar. Automatisierung
macht die **Ausführung** schneller, nicht die **Entscheidung** besser.
Was schnell ausgeführt wird, verliert auch schneller.
