# GStack (Garry Tan) — Installation und ein ehrlicher Befund

Geprüft am 08.09.2026, Linux-Container, Python 3.11 / Node 22 / bun.

```bash
git clone --single-branch --depth 1 \
  https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup
```

Beides lief durch, `./setup` mit **Exit 0**.

- Version **1.81.0.0**, Commit `0530392`
- **55 Skills** verlinkt nach `~/.claude/skills/`, plus Router-Alias `gstack`
- **57 gültige `SKILL.md`** (Frontmatter geprüft, 0 fehlerhaft)
- Playwright-Chromium 151.0.7922.34 heruntergeladen (184 MB + 115 MB)
- `browse`-Binär gebaut: 99 MB, startet und listet ~70 Unterbefehle
- `settings.json` wurde verändert — Sicherung liegt unter
  `settings.json.bak.20260908-062721.4133.9094`

## Die geforderten sieben Befehle — alle vorhanden

| Befehl | Zweck | SKILL.md |
|---|---|---|
| `/office-hours` | YC Office Hours, Produktdenken | 76 737 B |
| `/autoplan` | autonome Planung mit CEO/Design/Eng/DX-Review | 64 125 B |
| `/review` | Pre-Landing-PR-Review | 61 314 B |
| `/qa` | Web-App QA im echten Browser | 60 687 B |
| `/cso` | Chief Security Officer, Sicherheitsaudit | 61 655 B |
| `/ship` | Tests, Version, Changelog, Commit, PR | 78 048 B |
| `/gstack` | Router auf die passende Skill | 14 563 B |

Dazu 48 weitere, unter anderem `/spec`, `/investigate`, `/health`,
`/retro`, `/diagram`, `/make-pdf`, `/design-review`, `/plan-eng-review`,
die iOS-Kette und `/guard` / `/freeze` (Schreibschutz auf ein
Verzeichnis).

## Der Befund, der nicht in der Anleitung steht

**Die browsergestützten Skills funktionieren in dieser Umgebung nicht.**

```
browse goto https://example.com
→ net::ERR_CONNECTION_RESET
```

Der Egress-Proxy protokolliert dazu:

```
kind:   ws_closed_mid_exchange
detail: tunnel closed (code 1006) after 6s; 1727 B sent, 39 B received
host:   example.com:443
```

Das Tunnel wird also aufgebaut und dann mitten im TLS-Austausch
geschlossen. `browse` liest `HTTPS_PROXY` selbst aus — der Fehler liegt
nicht an GStack, sondern am Egress dieser Sandbox. Ein Versuch mit
explizitem `--proxy` scheiterte am Daemon-Konflikt
(`existing daemon has different config`), auch nach `disconnect`.

**Betroffen:** `/qa`, `/browse`, `/scrape`, `/design-review`,
`/design-shotgun`, `/pair-agent`, `/landing-report` — alles, was eine
Seite wirklich öffnen muss.

**Nicht betroffen:** `/office-hours`, `/autoplan`, `/spec`, `/review`,
`/cso`, `/ship`, `/investigate`, `/health`, `/retro` — die arbeiten auf
Quelltext und Git.

Auf deinem eigenen Rechner ohne diesen Proxy dürfte der Browser laufen.
Das ist eine begründete Erwartung, **keine Messung** — ich konnte es
hier nicht prüfen.

## Nicht eingerichtet

- **gbrain** — nicht erkannt, brain-Blöcke unterdrückt (`/setup-gbrain`)
- **Plan-tune-Hooks** — bei nicht-interaktivem Setup ausgelassen
  (`./setup --plan-tune-hooks`)
- **Aside-Browser** — macOS 15+, hier nicht verfügbar
- **Push-Schutz gegen Zugangsdaten** — steht auf `false`. Einschalten
  lohnt sich:
  ```bash
  ~/.claude/skills/gstack/bin/gstack-config set redact_prepush_hook true
  ```
