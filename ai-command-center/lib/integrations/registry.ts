/**
 * Register der optionalen Erweiterungen. Jede Integration ist Open Source und
 * wird über Umgebungsvariablen aktiviert. Reihenfolge = Anzeige-Reihenfolge.
 *
 * Betriebsmodell: Die App (Vercel/Next.js) ruft die selbst gehosteten Dienste
 * über HTTP an. So bleibt das bestehende System schlank und die Erweiterungen
 * sind pro Firma zu- und abschaltbar.
 */

import type { Integration } from "./types";

export const INTEGRATIONS: readonly Integration[] = [
  {
    id: "ollama",
    name: "Ollama (lokale KI-Modelle)",
    repo: "https://github.com/ollama/ollama",
    kind: "local-llm",
    zweck:
      "Eigene, lokale Sprachmodelle datenschutzfreundlich betreiben. Bindet sich über den bereits vorhandenen OpenAI-kompatiblen Provider an (LOCAL_LLM_URL → Ollama).",
    laufzeit: "binary",
    selbstGehostet: true,
    envKeys: ["LOCAL_LLM_URL"],
    healthUrlEnv: "LOCAL_LLM_URL",
    healthPfad: "/api/tags",
    abStufe: "PROFESSIONAL",
  },
  {
    id: "crewai",
    name: "CrewAI (Multi-Agent-Engine)",
    repo: "https://github.com/crewAIInc/crewAI",
    kind: "multi-agent",
    zweck:
      "Zusätzliche, rollenbasierte Multi-Agent-Workflows als externe Engine – ergänzt den bestehenden Orchestrator, ersetzt ihn nicht.",
    laufzeit: "python",
    selbstGehostet: true,
    envKeys: ["CREWAI_URL"],
    healthUrlEnv: "CREWAI_URL",
    healthPfad: "/health",
    abStufe: "PROFESSIONAL",
  },
  {
    id: "n8n",
    name: "n8n (Workflow-Automatisierung)",
    repo: "https://github.com/n8n-io/n8n",
    kind: "workflow",
    zweck:
      "Visuelle Automationen und Trigger. Missionen/Ergebnisse können n8n-Webhooks auslösen und umgekehrt.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["N8N_URL"],
    healthUrlEnv: "N8N_URL",
    healthPfad: "/healthz",
    abStufe: "BUSINESS",
  },
  {
    id: "chroma",
    name: "Chroma (Vektor-Speicher)",
    repo: "https://github.com/chroma-core/chroma",
    kind: "vector",
    zweck:
      "Vektor-Datenbank für Firmenwissen (Embeddings). Grundlage für die RAG-Suche.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["CHROMA_URL"],
    healthUrlEnv: "CHROMA_URL",
    healthPfad: "/api/v1/heartbeat",
    abStufe: "PROFESSIONAL",
  },
  {
    id: "haystack",
    name: "Haystack (RAG / Wissenssuche)",
    repo: "https://github.com/deepset-ai/haystack",
    kind: "rag",
    zweck:
      "Retrieval-Augmented-Generation über die Firmen-Wissensdatenbank; nutzt Chroma als Speicher.",
    laufzeit: "python",
    selbstGehostet: true,
    envKeys: ["HAYSTACK_URL"],
    healthUrlEnv: "HAYSTACK_URL",
    healthPfad: "/health",
    abStufe: "BUSINESS",
  },
  {
    id: "open-interpreter",
    name: "Open Interpreter (Computersteuerung)",
    repo: "https://github.com/OpenInterpreter/open-interpreter",
    kind: "computer-use",
    zweck:
      "Führt Code/Aktionen auf einer kontrollierten Maschine aus. Sicherheitskritisch – nur mit ausdrücklicher Freigabe (Human-in-the-Loop).",
    laufzeit: "python",
    selbstGehostet: true,
    envKeys: ["OPEN_INTERPRETER_URL"],
    healthUrlEnv: "OPEN_INTERPRETER_URL",
    healthPfad: "/health",
    abStufe: "ENTERPRISE",
    hinweis:
      "Führt echten Code aus. Nur in isolierter Umgebung und mit Freigabe je Schritt betreiben.",
  },
  {
    id: "playwright",
    name: "Playwright (Browser-Automatisierung)",
    repo: "https://github.com/microsoft/playwright",
    kind: "browser",
    zweck:
      "Browser-Automatisierung und Screenshots. Wird bereits für die Recherche-/Aufnahme-Funktionen genutzt.",
    laufzeit: "builtin",
    selbstGehostet: false,
    envKeys: [],
    immerAktiv: true,
    abStufe: "STARTER",
  },
  {
    id: "headroom",
    name: "Headroom (Token-/Kontext-Optimierung)",
    repo: "https://github.com/ai-boost/headroom",
    kind: "token-opt",
    zweck:
      "Reduziert Token-/Kontextverbrauch. Ergänzt das vorhandene Token-Budget-System des Orchestrators.",
    laufzeit: "lib",
    selbstGehostet: false,
    envKeys: [],
    immerAktiv: true,
    abStufe: "PERSONAL",
  },
  {
    id: "voicemode",
    name: "VoiceMode (Sprachsteuerung)",
    repo: "https://github.com/mbailey/voicemode",
    kind: "voice",
    zweck:
      "Sprachsteuerung/Diktat für die lokale Entwickler-/Bedien-Umgebung (Whisper + TTS).",
    laufzeit: "desktop",
    selbstGehostet: true,
    envKeys: ["VOICEMODE_URL"],
    abStufe: "ENTERPRISE",
    hinweis:
      "Braucht Mikrofon/Lautsprecher am lokalen Rechner – läuft nicht serverseitig/headless.",
  },
  {
    id: "voicebox",
    name: "Voicebox (Voice-Cloning / TTS)",
    repo: "https://github.com/jamiepine/voicebox",
    kind: "voice",
    zweck:
      "Sprachsynthese und Voice-Cloning (MCP). Kann Tutorial-/Ansage-Stimmen erzeugen, wenn als Dienst betrieben.",
    laufzeit: "desktop",
    selbstGehostet: true,
    envKeys: ["VOICEBOX_URL"],
    healthUrlEnv: "VOICEBOX_URL",
    healthPfad: "/health",
    abStufe: "ENTERPRISE",
    hinweis:
      "Desktop-App mit GUI; für serverseitige TTS als Dienst/MCP betreiben.",
  },
  {
    id: "tika",
    name: "Apache Tika (Datei-Textextraktion)",
    repo: "https://github.com/apache/tika",
    kind: "extract",
    zweck:
      "Extrahiert Text aus vielen Dateiformaten (Word, Excel, PowerPoint, PDF, RTF, ODF, E-Mail) – erweitert den Datei-Anhang über TXT/PDF hinaus.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["TIKA_URL"],
    healthUrlEnv: "TIKA_URL",
    healthPfad: "/version",
    abStufe: "STARTER",
  },
  {
    id: "searxng",
    name: "SearxNG (private Meta-Suche)",
    repo: "https://github.com/searxng/searxng",
    kind: "search",
    zweck:
      "Datenschutzfreundliche Meta-Suchmaschine als eigene Quelle für den KI-Browser – ohne Tracking und ohne externe Such-API.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["SEARXNG_URL"],
    healthUrlEnv: "SEARXNG_URL",
    healthPfad: "/healthz",
    abStufe: "PROFESSIONAL",
  },
  {
    id: "qdrant",
    name: "Qdrant (Vektor-Speicher)",
    repo: "https://github.com/qdrant/qdrant",
    kind: "vector",
    zweck:
      "Hochperformante Vektor-Datenbank als Alternative/Ergänzung zu Chroma – Grundlage für RAG über grosse Firmen-Wissensbestände.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["QDRANT_URL"],
    healthUrlEnv: "QDRANT_URL",
    healthPfad: "/healthz",
    abStufe: "PROFESSIONAL",
  },
  {
    id: "whisper",
    name: "Whisper (Sprache-zu-Text)",
    repo: "https://github.com/ggml-org/whisper.cpp",
    kind: "stt",
    zweck:
      "Transkribiert Audio-/Video-Aufnahmen (Kamera-Seite) in Text, der als Kontext an eine Mission gehängt werden kann.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["WHISPER_URL"],
    abStufe: "PROFESSIONAL",
    hinweis:
      "Als HTTP-Dienst betreiben (z. B. whisper.cpp-Server); wandelt Aufnahmen in Text um.",
  },
  {
    id: "flowise",
    name: "Flowise (visuelle LLM-Flows)",
    repo: "https://github.com/FlowiseAI/Flowise",
    kind: "workflow",
    zweck:
      "Visueller Baukasten für LLM-/Agenten-Abläufe. Ergänzt n8n um KI-spezifische Flows; per Webhook mit Missionen koppelbar.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["FLOWISE_URL"],
    healthUrlEnv: "FLOWISE_URL",
    healthPfad: "/api/v1/ping",
    abStufe: "BUSINESS",
  },
  {
    id: "minio",
    name: "MinIO (Datei-/Objektspeicher)",
    repo: "https://github.com/minio/minio",
    kind: "storage",
    zweck:
      "S3-kompatibler Objektspeicher für angehängte Dateien, Aufnahmen und erzeugte Artefakte – vollständig in der eigenen Infrastruktur.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["MINIO_URL"],
    healthUrlEnv: "MINIO_URL",
    healthPfad: "/minio/health/live",
    abStufe: "BUSINESS",
  },
  {
    id: "home-assistant",
    name: "Home Assistant (Geräte- & Anlagensteuerung)",
    repo: "https://github.com/home-assistant/core",
    kind: "automation",
    zweck:
      "Bindet echte Geräte, Maschinen und ganze Abteilungs-Abläufe an (Schalter, Schlösser, Sensoren, Aktoren, Industrieschnittstellen). Agenten können Zustände lesen und – nur nach ausdrücklicher Freigabe – Aktionen auslösen.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["HOMEASSISTANT_URL"],
    healthUrlEnv: "HOMEASSISTANT_URL",
    healthPfad: "/",
    abStufe: "ENTERPRISE",
    hinweis:
      "Steuert reale Hardware. Nur in kontrollierter Umgebung, mit Zugriffs-Token und Freigabe je Aktion (Human-in-the-Loop) betreiben.",
  },
  {
    id: "node-red",
    name: "Node-RED (Ereignis-/Anlagen-Automation)",
    repo: "https://github.com/node-red/node-red",
    kind: "automation",
    zweck:
      "Verknüpft Geräte, APIs und Missionen zu robusten Abläufen (Flows). Ideal, um eine ganze Abteilung ereignisgesteuert zu orchestrieren.",
    laufzeit: "service",
    selbstGehostet: true,
    envKeys: ["NODERED_URL"],
    healthUrlEnv: "NODERED_URL",
    healthPfad: "/",
    abStufe: "BUSINESS",
  },
];

/** Reihenfolge der Abo-Stufen (aufsteigend) für Verfügbarkeits-Vergleiche. */
export const STUFEN: readonly string[] = [
  "FREE",
  "PERSONAL",
  "STARTER",
  "PROFESSIONAL",
  "BUSINESS",
  "ENTERPRISE",
];

/** Integration per id holen. */
export function integrationById(id: string): Integration | undefined {
  return INTEGRATIONS.find((i) => i.id === id);
}

/** Alle Integrationen, die für eine Abo-Stufe verfügbar sind. */
export function integrationsFuerStufe(stufe: string): Integration[] {
  const rang = STUFEN.indexOf(stufe);
  if (rang < 0) return [];
  return INTEGRATIONS.filter((i) => STUFEN.indexOf(i.abStufe) <= rang);
}
