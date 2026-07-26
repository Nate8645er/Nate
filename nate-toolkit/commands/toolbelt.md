---
description: Zeigt, welche Werkzeuge in dieser Umgebung wirklich verfuegbar sind
---
Pruefe den tatsaechlichen Stand der Werkzeuge, statt ihn zu vermuten:

```bash
for t in rg fd bat uv ruff pre-commit pip-audit detect-secrets tmux node npm ffmpeg; do
  command -v $t >/dev/null && echo "DA:    $t ($($t --version 2>&1 | head -1))" || echo "fehlt: $t"
done
ls /usr/lib/postgresql/*/bin/postgres 2>/dev/null && echo "DA:    PostgreSQL"
ls /opt/pw-browsers/chromium 2>/dev/null && echo "DA:    Chromium"
```

Wenn ein GitHub-Repo "installiert" werden soll: erst klaeren, was es ist
(CLI-Werkzeug / Bibliothek / MCP-Server / Anwendung / Referenz-Codebasis) —
ein Repo ist kein Claude-Plugin. Siehe die Skill `dev-toolbelt`. Fuer die
~85 im Chat genannten Repos im Einzelnen: Skill `tool-catalog`.
