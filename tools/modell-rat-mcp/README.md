# Modell-Rat – Ultra-Team für Claude Code

Bindet mehrere Frontier-Modelle als **echte Worker-Werkzeuge** in Claude Code
ein. **Fable 5** (dein Haupt-Modell) ist der **Boss**: er ruft die Worker über
diese Tools auf und führt ihre Antworten zusammen. Die `ultra-*`-Subagenten
sind die ausführenden Assistenten.

## Das Team

| Tool | Modell | Anbieter | Zugang (Umgebungsvariable) |
|------|--------|----------|-----------------------------|
| `ask_gpt`      | GPT-5.6 Sol Ultra         | OpenAI          | `OPENAI_API_KEY` |
| `ask_sonnet`   | Claude Opus 4.8 / Fable 5 | Anthropic       | `ANTHROPIC_API_KEY` |
| `ask_gemini`   | Gemini 3.1 Pro Ultra      | Google DeepMind | `GOOGLE_API_KEY` |
| `ask_grok`     | Grok 4.5 Heavy            | xAI             | `XAI_API_KEY` |
| `ask_kimi`     | Kimi K3                   | Moonshot AI     | `MOONSHOT_API_KEY` |
| `ask_deepseek` | DeepSeek V4 Pro           | DeepSeek        | `DEEPSEEK_API_KEY` |
| `ask_qwen`     | Qwen 3.8 Max              | Alibaba Qwen    | `QWEN_API_KEY` |
| `ask_llama`    | Llama 4 Maverick          | Meta            | `META_LLM_URL` (+ optional `META_API_KEY`) |
| `ask_mistral`  | Mistral Large 3           | Mistral AI      | `MISTRAL_API_KEY` |
| `ask_glm`      | GLM-5                     | Zhipu AI        | `ZHIPU_API_KEY` |
| `ask_phi`      | Phi-4                     | Microsoft       | `PHI_API_KEY` / `PHI_URL` |
| `ask_cohere`   | Command A+                | Cohere          | `COHERE_API_KEY` |
| `ask_nemotron` | Nemotron Ultra            | NVIDIA          | `NVIDIA_API_KEY` |

Zusätzlich:
- `rat_status` – zeigt, welche Modelle einsatzbereit sind.
- `rat_council` – stellt allen bereiten Workern **dieselbe Frage parallel** und
  liefert alle Antworten gesammelt zurück (der Boss führt sie zusammen).

Noch nicht veröffentlichte Zielversionen (z. B. GPT-5.6, Gemini 3.1, GLM-5)
sind als Team-Platz angelegt; die exakte, real verfügbare Modell-ID setzt du per
`<PROVIDER>_MODEL`. Ohne gültigen Zugang bleibt der Platz ehrlich „Zugang nötig".

## Orchestrierungs-Frameworks (optional, im Team-Toolkit)

Zusätzlich zu den Modellen gehören diese Open-Source-Frameworks zum Fable-5-
Toolkit. Sie sind **aktiv, sobald sie installiert/konfiguriert** sind – Setup und
Referenz in `tools/agent-frameworks/README.md`:

| Framework | Zweck | Repo |
|-----------|-------|------|
| LangGraph | Graph-basierte KI-Orchestrierung | langchain-ai/langgraph |
| CrewAI | Multi-Agent-Team | crewAIInc/crewAI |
| Open Interpreter | Computer- & Code-Agent (nur mit Freigabe) | OpenInterpreter/open-interpreter |
| OpenAI Agents SDK | Agenten-Abläufe | openai/openai-agents-python |
| Qwen-Agent | Tool-/Agenten-Framework | QwenLM/Qwen-Agent |
| Llama Stack | Meta-Agenten-Stack | meta-llama/llama-stack |
| MCP Servers | Werkzeug-Brücke (Dateien, Git, u. v. m.) | modelcontextprotocol/servers |

## Ein Key für alle (empfohlen): OpenRouter

Statt dreizehn Einzel-Keys reicht **ein** OpenRouter-Key: er schaltet alle Worker
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
