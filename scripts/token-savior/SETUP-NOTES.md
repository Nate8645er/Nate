# Setup-Notizen: Token Savior v4.3 (token-savior-recall)

Eingerichtet am 2026-07-18 aus dem Upstream-Snapshot
[Mibayy/token-savior](https://github.com/Mibayy/token-savior) (main, v4.3).
Installiert wird das PyPI-Paket `token-savior-recall[mcp,memory-vector]`
in ein venv unter `~/.local/token-savior-venv`.

## Was Token Savior macht

1. **Strukturelle Code-Navigation** (MCP-Server): indexiert den Code nach
   Symbolen (Funktionen, Klassen, Call-Graph). Der Agent navigiert per
   Pointer (`find_symbol`, `get_function_source`, …) statt ganze Dateien
   zu lesen. Upstream-Benchmark: −80 % aktive Tokens, −83 % Wall-Time.
2. **Persistentes Memory**: Entscheidungen/Bugfixes/Konventionen in
   SQLite (FTS5 + Vektor-Embeddings via fastembed), kompakte Re-Injektion.
3. **Bash-Output-Kompaktierung** (PostToolUse-Hook, 34 Kompaktoren):
   git/gh/pytest/jest/tsc/docker/kubectl/aws/grep/find/cat/curl …
   Median −63 %; Hybrid-Modus sandboxt grosse Originale (abrufbar).
4. **Bash-Kommando-Rewriter** (PreToolUse-Hook, 10 sichere Regeln):
   `git status` → `--porcelain=v2 --branch`, `pytest` → `-q --tb=line`,
   `tsc` → `--pretty false` usw.

## Aktivierte Optimierungsstufe

- `TOKEN_SAVIOR_PROFILE=optimized` — vom Projekt empfohlenes
  Pareto-Optimum: 15 statt 69 Tools (~1,5 KT statt ~6 KT Manifest),
  thin inputSchema, Capture-Sandbox serverseitig aus, Memory-Hooks
  cross-project-sicher. (Das experimentelle Profil `auto` wurde bewusst
  NICHT aktiviert.)
- `TS_BASH_COMPACT=1` + `TS_BASH_REWRITE=1` (Session-Env in
  `.claude/settings.json`).

## Dateien in diesem Repo

| Datei | Zweck |
| --- | --- |
| `.mcp.json` | Registriert MCP-Server `token-savior` (Start via `launch.sh`), Profil `optimized`, `WORKSPACE_ROOTS=/home/user/Nate` |
| `scripts/token-savior/ensure-install.sh` | Installiert das venv bei Bedarf (idempotent; uv bevorzugt, pip-Fallback) |
| `scripts/token-savior/launch.sh` | Ensure-Install + exec MCP-Server |
| `scripts/token-savior/pre-hook.sh` | PreToolUse-Wrapper (Rewriter); No-op solange venv fehlt |
| `scripts/token-savior/post-hook.sh` | PostToolUse-Wrapper (Kompaktierung/Capture); No-op solange venv fehlt |
| `.claude/settings.json` | Env (`TS_BASH_COMPACT/REWRITE`) + Hooks (SessionStart-Warmup, PreToolUse, PostToolUse) |
| `.gitignore` | `.token-savior-cache.json` (Index-Cache) nicht committen |

Die Container sind ephemer, daher ist alles selbstheilend aufgebaut:
Der SessionStart-Hook installiert das venv im Hintergrund, `launch.sh`
installiert es notfalls synchron beim ersten MCP-Start, und die
Tool-Hooks sind stille No-ops, bis die Installation fertig ist.

## Abweichungen von `ts init --agent claude`

`ts init` schreibt absolute venv-Pfade und Timeouts in Millisekunden
(5000/2000) in die Settings. Stattdessen wurden repo-portable
Wrapper-Skripte mit `$CLAUDE_PROJECT_DIR` verwendet und Timeouts in
Sekunden (5/10) gesetzt (Claude-Code-Hooks interpretieren `timeout`
als Sekunden).

## Hinweis: Rewriter und Permissions

Der Rewriter beantwortet gematchte Bare-Kommandos (nur die 10 sicheren
Read-only-Regeln) mit `permissionDecision: allow` + `updatedInput` —
diese Kommandos laufen also ohne zusaetzlichen Prompt in der dichteren
Variante. Deaktivierbar via `TS_BASH_REWRITE=0`.

## Bekannte Einschraenkungen

- Das Memory (SQLite unter `~/.local/state/…`) uebersteht keinen
  Container-Wechsel — pro Session faengt es leer an. Symbol-Index wird
  pro Session neu aufgebaut (Sekunden).
- Erste Session pro Container: bis das venv installiert ist (~30-60 s),
  laufen Bash-Hooks als No-op; der MCP-Server blockiert seinen ersten
  Start bis zur fertigen Installation.
- fastembed laedt beim ersten Memory-Einsatz Modelle von Hugging Face
  (funktioniert durch den Egress-Proxy; ohne HF-Zugriff bleibt
  FTS5-Suche aktiv, nur Vektor-Suche entfaellt).

## Funktionstest (2026-07-18, dieser Container)

- MCP `initialize` ✓ (`token-savior-recall`), `tools/list` ✓ → 15 Tools
  (optimized), Log: `profile=optimized tools=15/69`
- `find_symbol("buildChromeArgs")` ✓ → 1-Zeilen-Pointer auf
  `superpowers-chrome/skills/browsing/lib/chrome-launcher-helpers.js:268`
- PreToolUse-Hook ✓: `git status` → `git status --porcelain=v2 --branch`
- PostToolUse-Hook ✓: git-Output kompaktiert (`[token-savior:compact]`)
