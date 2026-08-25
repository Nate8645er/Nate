# HOOKS — Uebersicht (Inhalt, nicht Mechanik)

Claude-Code-Hooks werden von der Claude-Code-Laufzeit ausgefuehrt (nicht vom Modell). Die **Mechanik** (SessionStart/PreToolUse/Stop) gibt es in OpenCode so nicht — der **Zweck** ist adaptierbar.

## Projekt-Hooks (`.claude/settings.json`)
| Hook | Ausloeser | Was | Portierbar |
|---|---|---|---|
| SessionStart → `scripts/omniroute-autostart.sh` | Sitzungsstart | startet OmniRoute im Hintergrund | ADAPTABLE (als Startskript) |

## Plugin-Hooks — `security-guidance` (David Dworken, Anthropic)
| Hook | Ausloeser | Was | Portierbar |
|---|---|---|---|
| PreToolUse | Edit/Write | Muster-Warnungen (unsichere Patterns) | CLAUDE_ONLY (Zweck als Lint-Regel adaptierbar) |
| Stop | Zug-Ende | LLM-Diff-Review | CLAUDE_ONLY |
| Commit-Review | vor Commit | Injection, XSS, SSRF, Secrets, IDOR, Auth-Bypass, Deserialisierung, Path-Traversal | CLAUDE_ONLY (Checkliste nutzbar) |

## Home-/Sitzungs-Hooks (`~/.claude/*.sh|*.py`) — CLAUDE_ONLY
- `session-start-git-identity.sh` — setzt Git-Identitaet der Remote-Sitzung.
- `stop-hook-git-check.sh` — erinnert an untracked/uncommitted Dateien.
- `stop-hook-reply-gate.py` — Antwort-Gate der Remote-Sitzung.
- `user-prompt-submit-reply-reminder.py` — Reply-Reminder.
→ Reine Claude-Code-Remote-Sitzungsinfrastruktur. Kein Secret, aber fuer OpenCode ohne Nutzen. **Nicht kopiert.**

## OpenCode-Adaption
- Security-Review: als eigener OpenCode-Schritt/Command vor dem Commit (Checkliste aus `../security-guidance`).
- OmniRoute-Autostart: `tools/omniroute-autostart.sh` als normales Startskript.
