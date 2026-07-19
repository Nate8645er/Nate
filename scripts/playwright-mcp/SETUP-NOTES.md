# Setup-Notizen: Playwright MCP (@playwright/mcp)

Eingerichtet am 2026-07-19. Quelle: offizielles npm-Paket
[`@playwright/mcp`](https://github.com/microsoft/playwright-mcp) via
`npx` (die hochgeladene ZIP war der main-Snapshot v0.0.78 und dient als
Referenz; das npm-Release ist der offizielle Installationsweg und bleibt
per npx in jeder frischen Session verfügbar).

## Anbindung

`.mcp.json` → Server `playwright` → `scripts/playwright-mcp/launch.sh`:

- erzeugt zur Laufzeit eine Playwright-MCP-Konfigdatei mit
  `browser.launchOptions`:
  - `executablePath: /opt/pw-browsers/chromium` (vorinstalliertes
    Chromium; verhindert Browser-Downloads, die in dieser Umgebung
    gesperrt sind — `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1`)
  - `headless` automatisch, wenn kein `DISPLAY` vorhanden
  - `chromiumSandbox: false` (Container läuft als root)
  - bei gesetztem `HTTPS_PROXY`: `--proxy-server=$HTTPS_PROXY` und
    `--ssl-version-max=tls1.2` (der Egress-Gateway resettet
    TLS-1.3-ClientHellos — gleiche Ursache wie beim
    superpowers-chrome-Setup, dort per Chrome-Netlog verifiziert)
- startet `npx -y @playwright/mcp@latest --config <datei>`
- Auf Systemen ohne diese Besonderheiten (lokaler Rechner mit Chrome,
  kein Proxy) verhält sich das Skript neutral.

## Koexistenz mit superpowers-chrome

Beide steuern Chromium, nutzen aber eigene Prozesse/Profile und stören
sich nicht. Playwright MCP bietet Accessibility-Snapshots, Formular-
und Netzwerk-Tools auf höherer Abstraktionsebene; superpowers-chrome
bietet rohes CDP + die `browsing`-Skill-CLI.

## Funktionstest (2026-07-19, dieser Container)

- `initialize` ✓ (Server „Playwright"), `tools/list` ✓ → 24 Tools
  (browser_navigate, browser_click, browser_snapshot,
  browser_take_screenshot, browser_fill_form, browser_network_requests, …)
- `browser_navigate https://example.com` ✓ → Titel „Example Domain"
- `browser_take_screenshot` ✓ → gültiges PNG (1280×720)

## Einschränkungen

- Erreichbare Domains sind durch die Egress-Policy der Umgebung begrenzt.
- Keine Login-Automatisierung in fremde Konten (2FA/Bot-Erkennung;
  Passwörter aus dem Chat werden grundsätzlich nicht verwendet).
