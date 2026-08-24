# wshobson/agents — installiert am 24.8.2026

Diese Sammlung (91 Plugins, 202 Agenten, 181 Skills, 105 Commands) liegt
jetzt im Repo unter `wshobson-agents/`. Sie bleibt damit erhalten, auch
wenn die Remote-Sitzung endet — das tut sie nur, weil sie im Git liegt.

## Was schon aktiv ist

17 Agenten, die zu deinem Geschaeft passen, liegen in `.claude/agents/`
und laden bei jeder Sitzung automatisch. Du musst dafuer nichts tun.

    Geschaeft      startup-analyst, business-analyst
    Inhalt         content-marketer, search-specialist
    Verkauf        sales-automator, customer-support
    SEO            zehn SEO-Agenten (Planer, Autor, Pruefer, Keyword,
                   Meta, Struktur, Snippet, Autoritaet, Auffrischung,
                   Kannibalisierung)
    Steuerung      context-manager

Du rufst sie im Chat einfach beim Namen, oder beschreibst die Aufgabe -
Claude Code waehlt dann den passenden.

## Was NICHT aktiv ist (mit Absicht)

Die restlichen rund 185 Agenten sind Entwickler- und Infrastruktur-
Spezialisten: Kubernetes, Terraform, Rust, Solidity, eingebettete
Firmware. Fuer einen Shop helfen die nicht, darum liegen sie nur im
Katalog und stehen dir nicht im Weg.

## Wie du mehr aktivierst (wenn du es je brauchst)

Ein Plugin nachinstallieren, mit allen seinen Commands und Skills:

    /plugin marketplace add ./wshobson-agents
    /plugin install <name>

Die Namen stehen in `wshobson-agents/.claude-plugin/marketplace.json`.

Oder einzelne Agenten von Hand aktivieren - eine Datei kopieren reicht:

    cp wshobson-agents/plugins/<plugin>/agents/<agent>.md .claude/agents/

## Was NICHT installiert wurde

Die Ordner fuer Cursor, Codex und andere Werkzeuge (`.cursor-plugin`,
`.github`, `tools`, `Makefile`) habe ich entfernt - du benutzt Claude
Code, der Rest waere nur Ballast gewesen.

## API-Schluessel

Keiner noetig. Diese Agenten sind Anweisungstexte fuer Claude Code, kein
eigener Dienst. Sie laufen mit demselben Zugang, den du schon hast.
