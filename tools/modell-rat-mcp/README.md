# Modell-Rat – Ultra-Team für Claude Code

Bindet mehrere Frontier-Modelle als **echte Worker-Werkzeuge** in Claude Code
ein. **Fable 5** (dein Haupt-Modell) ist der **Boss**: er ruft die Worker über
diese Tools auf und führt ihre Antworten zusammen. Die `ultra-*`-Subagenten
sind die ausführenden Assistenten.

## Das Team

| Tool | Modell | Anbieter | Zugang (Umgebungsvariable) |
|------|--------|----------|-----------------------------|
| `ask_gemini`   | Gemini 3 Ultra    | Google      | `GOOGLE_API_KEY` |
| `ask_grok`     | Grok 5            | xAI         | `XAI_API_KEY` |
| `ask_kimi`     | Kimi (Moonshot)   | Moonshot AI | `MOONSHOT_API_KEY` |
| `ask_qwen`     | Qwen 3 Max        | Alibaba     | `QWEN_API_KEY` |
| `ask_deepseek` | DeepSeek R2       | DeepSeek    | `DEEPSEEK_API_KEY` |
| `ask_llama`    | Llama 4 Behemoth  | Meta        | `META_LLM_URL` (+ optional `META_API_KEY`) |
| `ask_gpt`      | ChatGPT (GPT)     | OpenAI      | `OPENAI_API_KEY` |
| `ask_sonnet`   | Claude Sonnet 5   | Anthropic   | `ANTHROPIC_API_KEY` |
| `ask_mistral`  | Mistral Magistral | Mistral AI  | `MISTRAL_API_KEY` |

Zusätzlich:
- `rat_status` – zeigt, welche Modelle einsatzbereit sind.
- `rat_council` – stellt allen bereiten Workern **dieselbe Frage parallel** und
  liefert alle Antworten gesammelt zurück (der Boss führt sie zusammen).

## Ein Key für alle (empfohlen): OpenRouter

Statt neun Einzel-Keys reicht **ein** OpenRouter-Key: er schaltet alle Worker
frei. Setze `OPENROUTER_API_KEY` (holen unter https://openrouter.ai/keys) – der
Server leitet dann jeden Worker über OpenRouter (`provider/model`-Slugs, siehe
https://openrouter.ai/models). Ein zusätzlich gesetzter Einzel-Anbieter-Key hat
Vorrang vor OpenRouter. Die genauen Slugs sind per `<ID>_OR_SLUG` überschreibbar
(z. B. `GEMINI_OR_SLUG=google/gemini-3-ultra`).

## Ehrlichkeit

Ein Modell antwortet **nur**, wenn sein Zugang gesetzt ist. Fehlt der Key (bzw.
bei Llama die URL), meldet das Tool klar „nicht konfiguriert" – es wird nichts
vorgetäuscht. Prüfe jederzeit mit `rat_status`, wer wirklich mitarbeitet.

Alle Anbieter sprechen das OpenAI-kompatible Chat-Format (nur Anthropic weicht
ab, wird intern behandelt). Die exakte Modell-ID lässt sich pro Anbieter über
`<PROVIDER>_MODEL` überschreiben, z. B. `GOOGLE_MODEL=gemini-3-ultra`.

## Einrichtung – Keys sicher hinterlegen

Der Server ist bereits in `.mcp.json` (Repo-Wurzel) registriert. Du musst nur
deine Zugänge eintragen. **Keys niemals ins Git und niemals in den Chat** – der
saubere Weg ist eine lokale `.env`, die per `.gitignore` ausgeschlossen ist:

1. Kopiere `tools/modell-rat-mcp/.env.example` nach `tools/modell-rat-mcp/.env`.
2. Trage in die `.env` die Keys ein, die du nutzen willst (Links stehen drin).
   Nur ausgefüllte Zugänge werden aktiv; der Rest bleibt ehrlich inaktiv.
3. Starte Claude Code im Projekt neu. Der Server liest die `.env` automatisch
   (Tool-Ordner zuerst, dann Repo-Wurzel) und überschreibt dabei keine echten
   Umgebungsvariablen.

Alternativ (z. B. in einer gehosteten Umgebung) kannst du die gleichen Namen
auch als **Umgebungsvariablen/Secrets** setzen – die haben Vorrang vor der `.env`.

Eine `.env` mit echten Keys wird von Git ignoriert; committe sie nie manuell.

Schnelltest ohne Claude Code:

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"rat_status","arguments":{}}}' \
 | node tools/modell-rat-mcp/server.mjs
```

## Nutzung im Team

Sag dem Boss (Fable 5) einfach, das Team solle an einer Aufgabe arbeiten – oder
rufe den Agenten `fable5-boss` direkt auf. Er prüft `rat_status`, holt bei
schwierigen Entscheidungen `rat_council` ein, delegiert die Umsetzung an die
`ultra-*`-Spezialisten und lässt QA + Security prüfen, bevor etwas gilt.
