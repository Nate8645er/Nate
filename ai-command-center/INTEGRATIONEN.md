# Integrationen (optionale Erweiterungen)

Das AI Command Center bleibt schlank: die folgenden Open-Source-Module sind
**optional** und werden über Umgebungsvariablen aktiviert. Ohne Konfiguration
meldet jede Integration ehrlich „nicht verbunden" – nichts wird vorgetäuscht.

Betriebsmodell: Die App (Vercel/Next.js) ruft die selbst gehosteten Dienste
über HTTP an. Register + Status-Logik: `lib/integrations/`.

> Ehrliche Grenzen
> - **Sprache (VoiceMode/Voicebox)** braucht Audio-Hardware bzw. eine GUI und
>   läuft **nicht serverseitig/headless** – nur auf einem lokalen Rechner.
> - **Open Interpreter** führt echten Code aus – nur isoliert und mit Freigabe.
> - Diese Dienste werden **nicht** in die Serverless-App gebündelt; sie laufen
>   als eigene Container/Dienste auf Ihrer Infrastruktur.

## Übersicht

| Modul | Zweck | Aktivierung (ENV) | Ab Stufe |
|---|---|---|---|
| Ollama | lokale KI-Modelle | `LOCAL_LLM_URL` | Professional |
| CrewAI | Multi-Agent-Engine | `CREWAI_URL` | Professional |
| Chroma | Vektor-Speicher | `CHROMA_URL` | Professional |
| n8n | Workflow-Automatisierung | `N8N_URL` | Business |
| Haystack | RAG / Wissenssuche | `HAYSTACK_URL` | Business |
| Open Interpreter | Computersteuerung | `OPEN_INTERPRETER_URL` | Enterprise |
| VoiceMode | Sprachsteuerung (lokal) | `VOICEMODE_URL` | Enterprise |
| Voicebox | Voice-Cloning / TTS | `VOICEBOX_URL` | Enterprise |
| Apache Tika | Datei-Textextraktion (viele Formate) | `TIKA_URL` | Starter |
| SearxNG | private Meta-Suche (KI-Browser-Quelle) | `SEARXNG_URL` | Professional |
| Qdrant | Vektor-Speicher (Alternative zu Chroma) | `QDRANT_URL` | Professional |
| Whisper | Sprache-zu-Text (Aufnahmen → Text) | `WHISPER_URL` | Professional |
| Flowise | visuelle LLM-Flows | `FLOWISE_URL` | Business |
| MinIO | Datei-/Objektspeicher (S3-kompatibel) | `MINIO_URL` | Business |
| Node-RED | Ereignis-/Anlagen-Automation | `NODERED_URL` | Business |
| Home Assistant | Geräte- & Anlagensteuerung (Freigabe) | `HOMEASSISTANT_URL` | Enterprise |
| Playwright | Browser-Automatisierung | — (integriert) | Starter |
| Headroom | Token-/Kontext-Optimierung | — (integriert) | Personal |

Alle Module erscheinen im Arbeitsbereich unter **Mehr → Erweiterungen** mit
ehrlichem Verbindungsstatus (aus den Umgebungsvariablen abgeleitet). Ohne
hinterlegte Variable steht dort „nicht verbunden". Geräte-/Computersteuerung
(Home Assistant, Node-RED, Open Interpreter) nur mit Zugriffs-Token und Freigabe
je Aktion (Human-in-the-Loop) betreiben.

## Schnellstart (selbst gehostet)

Beispiel `docker-compose.integrations.yml` für die zentralen Dienste:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama:/root/.ollama"]

  chroma:
    image: chromadb/chroma:latest
    ports: ["8000:8000"]
    volumes: ["chroma:/chroma/chroma"]

  n8n:
    image: n8nio/n8n:latest
    ports: ["5678:5678"]
    environment:
      - N8N_PORT=5678

volumes:
  ollama:
  chroma:
```

Danach in `.env` der App eintragen:

```bash
LOCAL_LLM_URL=http://localhost:11434/v1   # Ollama (OpenAI-kompatibel) → Provider "local"
CHROMA_URL=http://localhost:8000
N8N_URL=http://localhost:5678
# optional:
CREWAI_URL=http://localhost:8100
HAYSTACK_URL=http://localhost:8200
OPEN_INTERPRETER_URL=http://localhost:8300
VOICEBOX_URL=http://localhost:8400
# weitere Erweiterungen (optional):
TIKA_URL=http://localhost:9998          # Apache Tika (Datei-Textextraktion)
SEARXNG_URL=http://localhost:8888       # SearxNG (private Meta-Suche)
QDRANT_URL=http://localhost:6333        # Qdrant (Vektor-Speicher)
WHISPER_URL=http://localhost:9000       # Whisper-Server (Sprache-zu-Text)
FLOWISE_URL=http://localhost:3100       # Flowise (visuelle LLM-Flows)
MINIO_URL=http://localhost:9001         # MinIO (Objektspeicher)
NODERED_URL=http://localhost:1880       # Node-RED (Anlagen-Automation)
HOMEASSISTANT_URL=http://localhost:8123 # Home Assistant (Geräte-/Anlagensteuerung)
```

CrewAI, Haystack und Open Interpreter sind Python-Dienste – als eigenen Container
mit schlanker HTTP-Schnittstelle (`/health`) betreiben und die URL oben setzen.
Tika, Qdrant, Flowise, MinIO, Node-RED und Home Assistant bieten fertige
Docker-Images; SearxNG und Whisper laufen ebenfalls als Container. Geräte-/
Anlagensteuerung (Home Assistant, Node-RED) nur mit Zugriffs-Token und Freigabe
je Aktion betreiben – die App löst nichts automatisch aus.

## Ollama (bereits nutzbar)

Ollama benötigt **keinen neuen Code**: Der vorhandene Provider `local`
(`lib/agents/providers.ts`) spricht OpenAI-kompatible Endpunkte. `LOCAL_LLM_URL`
auf die Ollama-URL setzen, Modell per `LOCAL_LLM_MODEL` wählen – fertig.

```bash
ollama pull qwen2.5:7b
export LOCAL_LLM_URL=http://localhost:11434/v1
export LOCAL_LLM_MODEL=qwen2.5:7b
```

## Sprachsteuerung von Claude Code (lokal, nicht in dieser App)

VoiceMode/Voicebox steuern **Claude Code auf Ihrem eigenen Rechner** (Mikrofon +
Lautsprecher). Auf dem lokalen Rechner:

```bash
# VoiceMode als Claude-Code-Plugin
claude plugin marketplace add mbailey/voicemode
claude plugin install voicemode@voicemode
/voicemode:install

# Voicebox (Voice-Studio, MCP)
git clone https://github.com/jamiepine/voicebox.git
cd voicebox && just setup
```

## Status im Code

```ts
import { INTEGRATIONS } from "@/lib/integrations/registry";
import { grundStatus, pingIntegration } from "@/lib/integrations/status";

grundStatus(INTEGRATIONS[0]);          // "nicht-konfiguriert" | "konfiguriert" | "bereit"
await pingIntegration(INTEGRATIONS[0]); // zusätzlich "aktiv", wenn erreichbar
```
