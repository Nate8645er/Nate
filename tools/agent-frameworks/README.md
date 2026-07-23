# Agent-Frameworks – Toolkit des Fable-5-Teams

Diese Open-Source-Frameworks erweitern das Fable-5-Team um zusätzliche
Orchestrierungs- und Ausführungs-Fähigkeiten (Graph-Abläufe, Multi-Agent-
Teams, Computer-/Code-Steuerung, Werkzeug-Brücken).

**Ehrlich:** Ein Framework ist erst dann wirklich aktiv, wenn es installiert und
– wo nötig – mit einem Modell-Zugang (siehe `tools/modell-rat-mcp/`) verbunden
ist. Diese Datei ist die reproduzierbare Einrichtung; nichts wird vorgetäuscht.

## Überblick

| Framework | Zweck | Repo | Sprache |
|-----------|-------|------|---------|
| LangGraph | Graph-basierte KI-Orchestrierung (Zustandsmaschinen für Agenten) | https://github.com/langchain-ai/langgraph | Python |
| CrewAI | Rollenbasierte Multi-Agent-Teams | https://github.com/crewAIInc/crewAI | Python |
| Open Interpreter | Computer- & Code-Agent (führt Code aus – NUR mit Freigabe) | https://github.com/OpenInterpreter/open-interpreter | Python |
| OpenAI Agents SDK | Agenten-Abläufe, Handoffs, Tools | https://github.com/openai/openai-agents-python | Python |
| Qwen-Agent | Tool-/Agenten-Framework (Alibaba) | https://github.com/QwenLM/Qwen-Agent | Python |
| Llama Stack | Meta-Agenten-/Inferenz-Stack | https://github.com/meta-llama/llama-stack | Python |
| MCP Servers | Werkzeug-Brücke (Dateien, Git, HTTP, DB …) | https://github.com/modelcontextprotocol/servers | TS/Python |

## Installation (in einer DAUERHAFTEN Umgebung)

> Hinweis: In der flüchtigen Web-Session verschwinden pip-Installationen beim
> Neustart des Containers. Führe die Installation dort aus, wo dein Team dauerhaft
> läuft (lokaler Rechner, eigener Server, persistenter Runner).

Python-Frameworks (empfohlen in einem venv):

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r tools/agent-frameworks/requirements.txt
```

MCP-Server (Node) nach Bedarf, z. B. der Dateisystem-Server:

```bash
npx -y @modelcontextprotocol/server-filesystem /pfad/zum/projekt
```

## Verbindung mit dem Team

- **Modelle:** Alle Frameworks nutzen dieselben Anbieter wie der Modell-Rat.
  Ein `OPENROUTER_API_KEY` (oder Einzel-Keys) genügt – siehe
  `tools/modell-rat-mcp/.env.example`.
- **Als MCP-Server einbinden:** Läuft ein Framework als MCP-Server, trage ihn in
  `.mcp.json` (Repo-Wurzel) neben `modell-rat` ein. Beispiel:

  ```json
  {
    "mcpServers": {
      "modell-rat": { "command": "node", "args": ["tools/modell-rat-mcp/server.mjs"] },
      "filesystem": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "."] }
    }
  }
  ```

- **Über den Boss:** Der Agent `fable5-boss` kennt diese Frameworks als Toolkit
  und delegiert passende Teilaufgaben – nutzt sie aber nur, wenn real
  eingerichtet.

## Sicherheit

**Open Interpreter** führt echten Code/Kommandos auf der Maschine aus. Nur in
isolierter Umgebung und mit ausdrücklicher Freigabe je Schritt betreiben
(Human-in-the-Loop). Das gilt sinngemäss für alle Werkzeuge mit Schreib-/
Ausführungsrechten.
