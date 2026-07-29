# WhatsApp-Plugin für Claude Code (Rich627/whatsapp-claude-plugin)

Verbindet Claude Code als **verknüpftes Gerät** mit deinem WhatsApp
(gleiches Protokoll wie WhatsApp Web, via Baileys). Nachrichten erreichen
die Session in Echtzeit, Claude antwortet von deiner eigenen Nummer.
Kein Business-API-Konto, kein Meta-Developer-Account, kein API-Schlüssel.

- Quelle: https://github.com/Rich627/whatsapp-claude-plugin (Apache 2.0)
- Geprüft am 2026-07-21: Code-Review sauber — keine Fremd-Server, Daten
  laufen nur zwischen WhatsApp und deinem Rechner. Einzige externe Aufrufe:
  optionale Sprach-Transkription (nur wenn man selbst einen Groq/OpenAI-Key
  setzt). Eingebauter Schutz gegen Prompt-Injection (Zugriffs-Freigaben
  können NIE per WhatsApp-Nachricht ausgelöst werden, nur im Terminal).

## Was es kann
- Nachrichten senden/empfangen, lange Antworten automatisch aufgeteilt
- Fotos, Sprachnachrichten, Videos, Dokumente, Sticker in beide Richtungen
- Zugriffskontrolle: Allowlist + Pairing-Codes — Fremde erreichen die
  Session nie
- Pro Gruppe eigene Persönlichkeit + Gedächtnis (config.md / memory.md)
- Werkzeug-Freigaben per Emoji-Reaktion (👍 / 👎) direkt aus WhatsApp
- Wiederkehrende Aufgaben (Cron) pro Gruppe
- `catch_up` nach Neustart: offene Aufgaben und unbeantwortete Chats

## Installation (Windows-PC, einmalig)

Voraussetzung: Claude Code installiert (siehe install.ps1), dazu Bun:

```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

Dann:

```powershell
claude plugin marketplace add Rich627/whatsapp-claude-plugin
claude plugin install whatsapp-claude-channel@whatsapp-claude-plugin
claude --dangerously-load-development-channels plugin:whatsapp-claude-channel@whatsapp-claude-plugin
```

Der dritte Befehl ist wichtig: Er startet Claude Code so, dass eine
eingehende WhatsApp-Nachricht die Session sofort aufweckt (Channel-Modus).

## Koppeln (braucht dein Handy)

1. In der Session: `/whatsapp-claude-channel:configure 41791234567`
   (Ländervorwahl + Nummer, ohne +)
2. Session beenden und mit dem dritten Befehl oben neu starten —
   der Pairing-Code erscheint automatisch.
3. Auf dem Handy: WhatsApp → Einstellungen → Verknüpfte Geräte →
   Gerät verknüpfen → **Stattdessen mit Telefonnummer verknüpfen** →
   Code eingeben.

Danach bleibt die Verbindung bestehen, auch wenn das Handy aus ist —
nur die Claude-Code-Session muss laufen. Diagnose bei Probleme:
`/whatsapp-claude-channel:doctor`

## Bekannte Stolpersteine (bei Installation 2026-07-21 gelöst)

Die Abhängigkeit `libsignal` kommt als git-Paket; wenn `bun install`
sie nicht laden kann (Firmen-Proxy), so beheben:

```sh
cd <plugin-ordner>   # z. B. ~/.claude/plugins/cache/whatsapp-claude-plugin/whatsapp-claude-channel/0.14.0
git clone --depth 1 https://github.com/whiskeysockets/libsignal-node.git vendor/libsignal-node
# in package.json ergänzen:  "overrides": { "libsignal": "file:./vendor/libsignal-node" }
npm install
# falls node_modules/libsignal ein toter Symlink ist:
rm node_modules/libsignal && cp -r vendor/libsignal-node node_modules/libsignal
cd node_modules/libsignal && npm install
# Start-Skript auf "bun server.ts" kürzen (ohne erneutes bun install)
```

Der `postinstall`-Schritt patcht Baileys automatisch (4 bekannte Bugs,
siehe patch-baileys.mjs) — der muss durchlaufen.

## Wichtig / ehrlich

- Das Pairing geht NUR mit dem Handy des Besitzers — niemand anders
  (auch keine KI) kann die Nummer ohne dich koppeln.
- Claude schreibt dann von DEINER Nummer. Für eine getrennte
  Bot-Identität eine eigene (Prepaid-)Nummer verwenden.
- In der Cloud-Session (dieser Container) ist das Plugin installiert und
  getestet, aber der Container ist flüchtig — die dauerhafte Nutzung
  gehört auf deinen eigenen PC (diese Anleitung).

## Verbindung zum AI Command Center

Unabhängig vom Plugin hat das verkaufte KI-System jetzt WhatsApp-Hilfen
für Unternehmen (ohne Kopplung, sofort nutzbar):
- Skill `/whatsapp` in der Kommandozentrale: versandfertige
  WhatsApp-Kundennachrichten (3 Varianten, Du/Sie).
- Kunden-CRM: Telefonfeld + „WhatsApp öffnen" (wa.me-Click-to-Chat mit
  vorbefüllter Begrüßung) + „WhatsApp-Text schreiben lassen".
