# Capital.com MCP (offiziell) — Einrichtung und ein Stolperstein

Repository: https://github.com/capital-com-sv/capital-mcp
Version 0.3.0, MIT, **offiziell von Capital.com** (verlinkt auf das
eigene Hilfecenter). Geprüft am 06.09.2026 in einer Linux-Umgebung,
Python 3.11.15.

---

## Der Stolperstein: fastmcp 4 bricht den Server

`pyproject.toml` verlangt `fastmcp>=0.2.0` — **ohne Obergrenze**. pip
installiert damit heute fastmcp 4.0.3, und dort ist
`fastmcp.tools.tool.ToolResult` verschwunden:

```
File "capital_mcp/error_handler.py", line 7, in <module>
    from fastmcp.tools.tool import ToolResult
ModuleNotFoundError: No module named 'fastmcp.tools.tool'
```

Eine frische Installation nach Anleitung scheitert also.

**Lösung, geprüft:**

```bash
pip install "fastmcp==3.4.7"
```

Getestet wurde auch 2.14.7 — dort fehlt `PrivateKeyJWTClientAuthenticator`,
der Import schlägt anders fehl. **3.4.7 ist die Version, mit der es
läuft.**

Falls beim Wechseln zwischen Versionen `ImportError: cannot import name
'FastMCP' from 'fastmcp' (unknown location)` auftaucht: Reste im
site-packages. Sauber machen:

```bash
pip uninstall -y fastmcp
rm -rf .venv/lib/python*/site-packages/fastmcp*
pip install --no-cache-dir "fastmcp==3.4.7"
```

---

## Einrichtung, die funktioniert hat

```bash
git clone https://github.com/capital-com-sv/capital-mcp.git
cd capital-mcp
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install "fastmcp==3.4.7"     # wichtig, siehe oben

cp .env.example .env                        # dann ausfuellen
```

Registrieren in Claude Code (offizieller Befehl aus `INSTALL.md`):

```bash
claude mcp add capitalcom -- /pfad/zu/capital-mcp/.venv/bin/python -m capital_mcp.server
```

`claude mcp list` muss danach `√ Connected` zeigen.

---

## Transport

**STDIO.** `INSTALL.md` Zeile 238: „Any STDIO-capable client works via
stdin/stdout JSON-RPC". Der Server meldet beim Start selbst
`transport 'stdio'`. Einen HTTP- oder Streamable-HTTP-Modus habe ich in
README, INSTALL und im Quellcode **nicht** gefunden — für Docker wird
ebenfalls `docker run -i` mit stdin verwendet.

---

## Was der Server kann

**38 Werkzeuge**, per `tools/list` ausgelesen:

- **Sitzung (4):** status, login, ping, logout
- **Märkte (6):** search, get, navigation_root, navigation_node, prices,
  sentiment
- **Konto (6):** list, preferences_get/set, history_activity,
  history_transactions, demo_topup
- **Handel (13):** positions_list/get, orders_list, confirm_get/wait,
  preview_position, preview_working_order,
  preview_working_order_update, **execute_position**,
  **execute_working_order**, execute_working_order_update,
  **positions_close**, **orders_cancel**
- **Watchlists (6)** · **Streaming (3):** prices, alerts, portfolio

Die fett markierten bewegen echtes Geld.

## Sicherheitsmodell

Aus `.env.example`, und es ist ordentlich gebaut:

| Variable | Vorgabe | Wirkung |
|---|---|---|
| `CAP_ALLOW_TRADING` | `false` | Handel komplett aus |
| `CAP_ALLOWED_EPICS` | leer | leer = jeder Handel blockiert |
| `CAP_DRY_RUN` | `false` | auf `true` setzen: keine Ausführung |
| `CAP_REQUIRE_EXPLICIT_CONFIRM` | `true` | Zwei-Stufen-Ausführung |
| `CAP_MAX_POSITION_SIZE` | `1.0` | Grössenlimit |
| `CAP_MAX_OPEN_POSITIONS` | `3` | Positionslimit |
| `CAP_MAX_ORDERS_PER_DAY` | `20` | Tageslimit |

Das README sagt es selbst: **Demokonto zuerst.** Und: „API keys are
trading-capable; Capital.com doesn't offer read-only keys" — es gibt
keinen Nur-Lese-Schlüssel.

---

## Was für einen Schlüssel nötig ist

1. Konto auf capital.com, **Demo** zum Testen
2. **2FA aktivieren** — Voraussetzung für API-Schlüssel
3. Settings → API integrations → Generate new key
4. Eigenes API-Passwort setzen (**nicht** das Plattform-Passwort)
5. Der Schlüssel wird **nur einmal angezeigt**

Diese drei Werte gehören in die `.env`:
`CAP_API_KEY`, `CAP_IDENTIFIER` (Login-Mail), `CAP_API_PASSWORD`.

`.env` steht in der `.gitignore` des Projekts — geprüft.
