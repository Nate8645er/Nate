# Blin — der lokale Agent (die „echte" Version aus dem Video)

Das Web-Cockpit (`../app/index.html`) ist das **Gesicht** von Blin. Dieser
Ordner ist der **Koerper**: ein Programm, das auf DEINEM Rechner laeuft und
Dinge wirklich tut — Tages-Dashboard im Terminal + echte Browser-Steuerung.

## Warum nicht die Webseite?

Eine Webseite ist vom Browser eingesperrt und darf den Computer nicht
fernsteuern. Das Video („Jarvis bedient den Laptop") zeigt ein **lokales
Programm mit Computer-Zugriff**, keine Webseite. Deshalb gibt es Blin hier
als echtes Programm.

## Ehrliche Grenzen

- **Tages-Dashboard**: laeuft ueberall mit Node — echt.
- **Browser-Steuerung** (`--browse`): oeffnet einen echten Browser, navigiert,
  macht Screenshots — echt (Playwright). Auf deinem Mac ohne Sandbox-Proxy
  navigiert er direkt ins Web.
- **„Den ganzen Laptop per Stimme steuern"** (beliebige Apps oeffnen, tippen):
  das ist **Computer-Use ueber Claude Code**, nicht dieses kleine Skript.
  Blin hier deckt Dashboard + Web ab; fuer Vollzugriff nutzt du Claude Code
  auf deinem Rechner.
- **Kein Auto-Umsatz, kein Offline-Zauber.** Aktionen mit Aussenwirkung erst
  nach deiner Freigabe. Security defensiv.

## Setup (einmalig, am Mac)

```bash
# Node 18+ vorausgesetzt (node -v)
cd ultra-enterprise-os/blin
npm init -y >/dev/null 2>&1
npm i playwright-core          # nur fuer --browse noetig
npx playwright install chromium
cp tasks.example.json tasks.json   # dann tasks.json mit deinem Tag fuellen
```

## Nutzung

```bash
node blin.mjs                 # Live-Tages-Dashboard (Countdown, Aufgaben)
node blin.mjs --once          # einmal rendern
node blin.mjs --browse "whey protein bestseller"      # echter Browser + Suche
node blin.mjs --browse "…" --headless                 # ohne Fenster (Test)
```

## Schluessel & Sicherheit

- API-Keys kommen aus **Umgebungsvariablen**, nie in den Code:
  `export ANTHROPIC_API_KEY=…` (fuer spaetere Claude-Anbindung).
- Die ElevenLabs-Stimme wird im Web-Cockpit gesetzt und **nur im Browser**
  gespeichert (localStorage) — nie hier im Code.
- `node_modules/`, `tasks.json` und Screenshots sind aus Git ausgeschlossen.

## Blin per Siri auf dem iPhone

`siri-shortcut.md` ist die komplette Schritt-für-Schritt-Anleitung fuer
einen Siri-Kurzbefehl „Blin": du sagst „Hey Siri, Blin", sprichst deine
Frage, Blin denkt (Claude/Fable 5) und antwortet mit deiner ElevenLabs-
Stimme. Keys werden nur auf dem iPhone in der Kurzbefehle-App gespeichert,
nie im Code.

## Wie es „1:1 wie im Video" wird

1. `blin.mjs` liefert das Dashboard (linker/rechter Monitor im Video).
2. Fuer echtes Handeln (surfen, Formulare, Recherche) treibt Blin den Browser.
3. Fuer „bedient den ganzen Laptop": in **Claude Code** auf deinem Mac mit
   Computer-Use — dort hat der Agent die noetigen Rechte, die eine Webseite
   nie bekommt. Der `/blin-morning`-Command startet die Morgen-Routine.
