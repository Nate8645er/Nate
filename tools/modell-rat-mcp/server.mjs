#!/usr/bin/env node
/**
 * Modell-Rat – MCP-Server für Claude Code.
 *
 * Bindet mehrere Frontier-Modelle als echte Werkzeuge (Worker) in Claude Code
 * ein. Der Haupt-Agent (Fable 5) ist der Boss: er ruft die Worker über diese
 * Tools auf und führt ihre Antworten zusammen.
 *
 * Ehrlich: Ein Modell antwortet nur, wenn sein API-Key (bzw. bei Llama die
 * URL) als Umgebungsvariable gesetzt ist. Fehlt der Zugang, meldet das Tool
 * klar „nicht konfiguriert" – es wird nichts vorgetäuscht.
 *
 * Protokoll: MCP über stdio (JSON-RPC 2.0, zeilenweise). Keine Abhängigkeiten.
 *
 * Zugänge (Umgebungsvariablen) – setze die, die du nutzen willst:
 *   OPENAI_API_KEY     GPT-5.6 Sol Ultra (OpenAI)
 *   ANTHROPIC_API_KEY  Claude Opus 4.8 / Fable 5 (Anthropic)
 *   GOOGLE_API_KEY     Gemini 3.1 Pro Ultra (Google DeepMind)
 *   XAI_API_KEY        Grok 4.5 Heavy (xAI)
 *   MOONSHOT_API_KEY   Kimi K3 (Moonshot AI)
 *   DEEPSEEK_API_KEY   DeepSeek V4 Pro
 *   QWEN_API_KEY       Qwen 3.8 Max (Alibaba)
 *   META_LLM_URL       Llama 4 Maverick (Endpoint eines OpenAI-kompatiblen Hosts), META_API_KEY optional
 *   MISTRAL_API_KEY    Mistral Large 3
 *   ZHIPU_API_KEY      GLM-5 (Zhipu AI)
 *   PHI_API_KEY/PHI_URL Phi-4 (Microsoft; Host-URL oder Azure/GitHub-Models)
 *   COHERE_API_KEY     Command A+ (Cohere)
 *   NVIDIA_API_KEY     Nemotron Ultra (NVIDIA NIM)
 *   OPENROUTER_API_KEY EIN Key für alle (Fallback über OpenRouter)
 * Modell-ID optional überschreibbar per <PROVIDER>_MODEL (z. B. GOOGLE_MODEL).
 * Exakte, noch nicht veröffentlichte Versionen per <PROVIDER>_MODEL setzen,
 * sobald der Anbieter sie ausliefert – bis dahin ehrlich „Zugang nötig".
 */

import process from "node:process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const REQUEST_TIMEOUT_MS = 90_000;
const MAX_TOKENS = 2048;

/**
 * Lädt Zugänge aus lokalen .env-Dateien (Tool-Ordner + Repo-Wurzel), OHNE
 * bereits gesetzte Umgebungsvariablen zu überschreiben. Diese Dateien sind per
 * .gitignore ausgeschlossen – so trägt der Nutzer seine Keys lokal ein, ohne
 * dass sie je ins Git oder in den Chat gelangen. Parser bewusst minimal
 * (KEY=VALUE, # Kommentare, optionale Anführungszeichen, optionales export).
 */
function ladeEnvDatei(pfad) {
  let inhalt;
  try {
    inhalt = readFileSync(pfad, "utf8");
  } catch {
    return; // Datei fehlt → egal, dann greifen echte Env-Variablen.
  }
  for (const roh of inhalt.split("\n")) {
    const zeile = roh.trim();
    if (!zeile || zeile.startsWith("#")) continue;
    const ohneExport = zeile.replace(/^export\s+/, "");
    const gleich = ohneExport.indexOf("=");
    if (gleich < 1) continue;
    const name = ohneExport.slice(0, gleich).trim();
    let wert = ohneExport.slice(gleich + 1).trim();
    if ((wert.startsWith('"') && wert.endsWith('"')) || (wert.startsWith("'") && wert.endsWith("'"))) {
      wert = wert.slice(1, -1);
    }
    if (name && process.env[name] === undefined) process.env[name] = wert;
  }
}
const HIER = dirname(fileURLToPath(import.meta.url));
ladeEnvDatei(join(HIER, ".env")); // tools/modell-rat-mcp/.env
ladeEnvDatei(join(HIER, "..", "..", ".env")); // Repo-Wurzel/.env

/**
 * Worker-Registry: id -> Konfiguration. Reihenfolge = Anzeigereihenfolge.
 * `orSlug` = Modell-Slug bei OpenRouter (ein Key für alle); per <ID>_OR_SLUG
 * überschreibbar. Aktuelle Slugs bei Bedarf auf https://openrouter.ai/models
 * prüfen.
 */
const MODELS = {
  gpt: { label: "GPT-5.6 Sol Ultra", vendor: "OpenAI", style: "openai", url: "https://api.openai.com/v1/chat/completions", keyEnv: "OPENAI_API_KEY", model: "gpt-5.6-sol-ultra", modelEnv: "OPENAI_MODEL", orSlug: "openai/gpt-4o" },
  sonnet: { label: "Claude Opus 4.8 / Fable 5", vendor: "Anthropic", style: "anthropic", url: "https://api.anthropic.com/v1/messages", keyEnv: "ANTHROPIC_API_KEY", model: "claude-opus-4-8", modelEnv: "SONNET_MODEL", orSlug: "anthropic/claude-sonnet-4.5" },
  gemini: { label: "Gemini 3.1 Pro Ultra", vendor: "Google DeepMind", style: "openai", url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", keyEnv: "GOOGLE_API_KEY", model: "gemini-3.1-pro-ultra", modelEnv: "GOOGLE_MODEL", orSlug: "google/gemini-2.5-pro" },
  grok: { label: "Grok 4.5 Heavy", vendor: "xAI", style: "openai", url: "https://api.x.ai/v1/chat/completions", keyEnv: "XAI_API_KEY", model: "grok-4.5-heavy", modelEnv: "XAI_MODEL", orSlug: "x-ai/grok-4" },
  kimi: { label: "Kimi K3", vendor: "Moonshot AI", style: "openai", url: "https://api.moonshot.ai/v1/chat/completions", keyEnv: "MOONSHOT_API_KEY", model: "kimi-k3", modelEnv: "MOONSHOT_MODEL", orSlug: "moonshotai/kimi-k2" },
  deepseek: { label: "DeepSeek V4 Pro", vendor: "DeepSeek", style: "openai", url: "https://api.deepseek.com/v1/chat/completions", keyEnv: "DEEPSEEK_API_KEY", model: "deepseek-v4-pro", modelEnv: "DEEPSEEK_MODEL", orSlug: "deepseek/deepseek-r1" },
  qwen: { label: "Qwen 3.8 Max", vendor: "Alibaba Qwen", style: "openai", url: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions", keyEnv: "QWEN_API_KEY", model: "qwen3.8-max", modelEnv: "QWEN_MODEL", orSlug: "qwen/qwen3-max" },
  llama: { label: "Llama 4 Maverick", vendor: "Meta", style: "openai", urlEnv: "META_LLM_URL", url: "", keyEnv: "META_API_KEY", model: "llama-4-maverick", modelEnv: "META_MODEL", keyOptional: true, orSlug: "meta-llama/llama-4-maverick" },
  mistral: { label: "Mistral Large 3", vendor: "Mistral AI", style: "openai", url: "https://api.mistral.ai/v1/chat/completions", keyEnv: "MISTRAL_API_KEY", model: "mistral-large-3", modelEnv: "MISTRAL_MODEL", orSlug: "mistralai/mistral-large-2411" },
  glm: { label: "GLM-5", vendor: "Zhipu AI", style: "openai", url: "https://open.bigmodel.cn/api/paas/v4/chat/completions", keyEnv: "ZHIPU_API_KEY", model: "glm-5", modelEnv: "ZHIPU_MODEL", orSlug: "z-ai/glm-4.6" },
  phi: { label: "Phi-4", vendor: "Microsoft", style: "openai", urlEnv: "PHI_URL", url: "https://models.inference.ai.azure.com/chat/completions", keyEnv: "PHI_API_KEY", model: "phi-4", modelEnv: "PHI_MODEL", orSlug: "microsoft/phi-4" },
  cohere: { label: "Command A+", vendor: "Cohere", style: "openai", url: "https://api.cohere.ai/compatibility/v1/chat/completions", keyEnv: "COHERE_API_KEY", model: "command-a-plus", modelEnv: "COHERE_MODEL", orSlug: "cohere/command-a" },
  nemotron: { label: "Nemotron Ultra", vendor: "NVIDIA", style: "openai", url: "https://integrate.api.nvidia.com/v1/chat/completions", keyEnv: "NVIDIA_API_KEY", model: "nvidia/llama-3.1-nemotron-ultra-253b-v1", modelEnv: "NVIDIA_MODEL", orSlug: "nvidia/llama-3.1-nemotron-ultra-253b-v1" },
};

/** OpenRouter: EIN Key für alle Modelle (OpenAI-kompatibel). Aktiv, sobald
 *  OPENROUTER_API_KEY gesetzt ist – dann laufen alle Worker ohne Direkt-Key darüber. */
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
function openrouterKey() {
  return envClean("OPENROUTER_API_KEY");
}
function orSlugOf(m, id) {
  return envClean(`${id.toUpperCase()}_OR_SLUG`) || m.orSlug;
}

/**
 * Liest eine Umgebungsvariable und behandelt Leerwerte UND nicht aufgelöste
 * Platzhalter (z. B. der Literal-String "${GOOGLE_API_KEY}", wenn eine
 * .mcp.json-env-Zuweisung nicht expandiert wurde) als NICHT gesetzt. So bleibt
 * der Status ehrlich: nur ein echter Zugang zählt als „bereit".
 */
function envClean(name) {
  const v = (process.env[name] || "").trim();
  if (!v) return "";
  if (/^\$\{[^}]*\}$/.test(v) || /^\$[A-Z_][A-Z0-9_]*$/.test(v)) return ""; // unaufgelöster Platzhalter
  return v;
}
/** Effektive Endpoint-URL (Env-Override vor Standard). */
function urlOf(m) {
  if (m.urlEnv) {
    const o = envClean(m.urlEnv);
    if (o) return o;
  }
  return m.url;
}
/** API-Key (getrimmt) oder leer. */
function keyOf(m) {
  return envClean(m.keyEnv);
}
/** Effektive Modell-ID (Env-Override vor Standard). */
function modelOf(m) {
  return (m.modelEnv && envClean(m.modelEnv)) || m.model;
}
/** Direkt-Zugang vorhanden? Cloud: Key gesetzt. Selbst gehostet: URL gesetzt. */
function directReady(m) {
  if (m.keyOptional) return Boolean(urlOf(m));
  return Boolean(keyOf(m)) && Boolean(urlOf(m));
}
/** Einsatzbereit = eigener Zugang ODER OpenRouter-Key (ein Key für alle). */
function ready(m) {
  return directReady(m) || Boolean(openrouterKey());
}
/** Wie wird das Modell erreicht? Für die ehrliche Statusanzeige. */
function modus(m) {
  if (directReady(m)) return "direkt";
  if (openrouterKey()) return "OpenRouter";
  return "";
}

/** Führt einen einzelnen OpenAI-/Anthropic-Request aus und parst die Antwort. */
async function httpCall(url, headers, body, anthropic) {
  try {
    const res = await fetch(url, { method: "POST", headers, body: JSON.stringify(body), signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
    if (!res.ok) {
      let detail = "";
      try { detail = (await res.text()).slice(0, 200); } catch { /* egal */ }
      return { ok: false, error: `HTTP ${res.status}: ${detail}` };
    }
    const data = await res.json();
    const text = anthropic ? extractAnthropic(data) : extractOpenAI(data);
    return text ? { ok: true, text } : { ok: false, error: "leere/unerwartete Antwort" };
  } catch (err) {
    const reason = err && err.name === "TimeoutError" ? `Timeout nach ${REQUEST_TIMEOUT_MS / 1000}s` : String(err && err.message || err);
    return { ok: false, error: `Netzwerkfehler (${reason})` };
  }
}

/**
 * Ruft ein Modell einmal auf. Bevorzugt den Direkt-Zugang; ist keiner gesetzt,
 * aber OPENROUTER_API_KEY vorhanden, läuft der Aufruf über OpenRouter (ein Key
 * für alle). Gibt { ok, text } oder { ok:false, error } zurück – wirft nie.
 */
async function callModel(m, prompt, id) {
  const msgs = [{ role: "user", content: prompt }];

  if (!directReady(m)) {
    const orKey = openrouterKey();
    if (!orKey) return { ok: false, error: `nicht konfiguriert – setze ${m.keyOptional ? m.urlEnv : m.keyEnv} oder OPENROUTER_API_KEY` };
    const headers = { "content-type": "application/json", authorization: `Bearer ${orKey}`, "X-Title": "Modell-Rat" };
    const body = { model: orSlugOf(m, id), max_tokens: MAX_TOKENS, messages: msgs };
    return httpCall(OPENROUTER_URL, headers, body, false); // OpenRouter ist immer OpenAI-Format
  }

  const url = urlOf(m);
  const key = keyOf(m);
  const model = modelOf(m);
  let headers, body;
  if (m.style === "anthropic") {
    headers = { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01" };
    body = { model, max_tokens: MAX_TOKENS, messages: msgs };
  } else {
    headers = { "content-type": "application/json" };
    if (key) headers.authorization = `Bearer ${key}`;
    body = { model, max_tokens: MAX_TOKENS, messages: msgs };
  }
  return httpCall(url, headers, body, m.style === "anthropic");
}

function extractOpenAI(data) {
  const c = data && data.choices;
  if (!Array.isArray(c) || !c.length) return null;
  const content = c[0] && c[0].message && c[0].message.content;
  return typeof content === "string" && content.length ? content : null;
}
function extractAnthropic(data) {
  const content = data && data.content;
  if (!Array.isArray(content)) return null;
  const text = content.filter((b) => b && b.type === "text" && typeof b.text === "string").map((b) => b.text).join("");
  return text.length ? text : null;
}

/* ------------------------------- MCP-Tools ------------------------------- */

/** Baut die Tool-Liste: pro Modell ein ask_<id> + rat_status + rat_council. */
function toolList() {
  const tools = [];
  for (const [id, m] of Object.entries(MODELS)) {
    tools.push({
      name: `ask_${id}`,
      description: `Worker ${m.label} (${m.vendor}) eine Frage stellen und die Antwort erhalten. ${ready(m) ? `Bereit (${modus(m)}).` : `Nicht konfiguriert – setze ${m.keyOptional ? m.urlEnv : m.keyEnv} oder OPENROUTER_API_KEY.`}`,
      inputSchema: {
        type: "object",
        properties: { prompt: { type: "string", description: "Die Frage/Aufgabe an das Modell (Deutsch oder Englisch)." } },
        required: ["prompt"],
      },
    });
  }
  tools.push({
    name: "rat_status",
    description: "Zeigt alle Modelle des Rats und welche einsatzbereit (Zugang gesetzt) sind.",
    inputSchema: { type: "object", properties: {} },
  });
  tools.push({
    name: "rat_council",
    description: "Stellt allen einsatzbereiten Worker-Modellen (oder einer Auswahl) DIESELBE Frage parallel und liefert alle Antworten gesammelt zurück – damit der Boss (Fable 5) sie zusammenführen kann.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: { type: "string", description: "Die Frage/Aufgabe an den ganzen Rat." },
        models: { type: "array", items: { type: "string" }, description: `Optional: Auswahl von Modell-Ids (${Object.keys(MODELS).join(", ")}). Leer = alle einsatzbereiten.` },
      },
      required: ["prompt"],
    },
  });
  return tools;
}

/** Führt einen Tool-Aufruf aus und liefert den Antworttext. */
async function runTool(name, args) {
  if (name === "rat_status") {
    const or = Boolean(openrouterKey());
    const zeilen = Object.entries(MODELS).map(([id, m]) => {
      if (!ready(m)) return `· Zugang nötig  ${id.padEnd(9)} ${m.label} (${m.vendor}) – setze ${m.keyOptional ? m.urlEnv : m.keyEnv} oder OPENROUTER_API_KEY`;
      const md = modus(m);
      const modell = md === "OpenRouter" ? orSlugOf(m, id) : modelOf(m);
      return `✓ bereit   ${id.padEnd(9)} ${m.label} (${m.vendor}) → ${modell} [${md}]`;
    });
    const n = Object.values(MODELS).filter(ready).length;
    const kopf = or
      ? `Modell-Rat: ${n} von ${Object.keys(MODELS).length} einsatzbereit (OpenRouter aktiv – ein Key für alle).`
      : `Modell-Rat: ${n} von ${Object.keys(MODELS).length} einsatzbereit.`;
    return `${kopf}\n\n${zeilen.join("\n")}`;
  }

  if (name === "rat_council") {
    const prompt = String(args && args.prompt || "").trim();
    if (!prompt) return "Fehler: prompt fehlt.";
    const auswahl = Array.isArray(args && args.models) && args.models.length
      ? args.models.map(String).filter((id) => Object.prototype.hasOwnProperty.call(MODELS, id))
      : Object.keys(MODELS);
    const aktive = auswahl.filter((id) => ready(MODELS[id]));
    if (!aktive.length) return "Kein Worker einsatzbereit. Setze mindestens einen Zugang (siehe rat_status).";
    const ergebnisse = await Promise.all(aktive.map(async (id) => {
      const r = await callModel(MODELS[id], prompt, id);
      return { id, label: MODELS[id].label, r };
    }));
    const teile = ergebnisse.map(({ label, r }) => `=== ${label} ===\n${r.ok ? r.text : `[Fehler: ${r.error}]`}`);
    return `Antworten von ${aktive.length} Worker-Modell(en) auf dieselbe Frage:\n\n${teile.join("\n\n")}`;
  }

  if (name.startsWith("ask_")) {
    const id = name.slice(4);
    if (!Object.prototype.hasOwnProperty.call(MODELS, id)) return `Unbekanntes Modell: ${id}`;
    const m = MODELS[id];
    const prompt = String(args && args.prompt || "").trim();
    if (!prompt) return "Fehler: prompt fehlt.";
    const r = await callModel(m, prompt, id);
    return r.ok ? r.text : `[${m.label} nicht verfügbar: ${r.error}]`;
  }

  return `Unbekanntes Tool: ${name}`;
}

/* ----------------------------- MCP über stdio ---------------------------- */

const PROTOCOL_VERSION = "2024-11-05";

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}
function result(id, res) {
  send({ jsonrpc: "2.0", id, result: res });
}
function errorReply(id, code, message) {
  send({ jsonrpc: "2.0", id, error: { code, message } });
}

async function handle(msg) {
  const { id, method, params } = msg;
  // Notifications (keine id) nie beantworten.
  if (method === "initialize") {
    result(id, {
      protocolVersion: (params && params.protocolVersion) || PROTOCOL_VERSION,
      capabilities: { tools: {} },
      serverInfo: { name: "modell-rat", version: "1.0.0" },
    });
    return;
  }
  if (method === "notifications/initialized" || method === "initialized") return;
  if (method === "ping") { if (id !== undefined) result(id, {}); return; }
  if (method === "tools/list") { result(id, { tools: toolList() }); return; }
  if (method === "tools/call") {
    const name = params && params.name;
    const args = (params && params.arguments) || {};
    try {
      const text = await runTool(name, args);
      result(id, { content: [{ type: "text", text }] });
    } catch (err) {
      result(id, { content: [{ type: "text", text: `Interner Fehler: ${String(err && err.message || err)}` }], isError: true });
    }
    return;
  }
  if (id !== undefined) errorReply(id, -32601, `Unbekannte Methode: ${method}`);
}

let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;
  let nl;
  while ((nl = buffer.indexOf("\n")) !== -1) {
    const line = buffer.slice(0, nl).trim();
    buffer = buffer.slice(nl + 1);
    if (!line) continue;
    let msg;
    try { msg = JSON.parse(line); } catch { continue; }
    handle(msg).catch((err) => {
      if (msg && msg.id !== undefined) errorReply(msg.id, -32603, String(err && err.message || err));
    });
  }
});
process.stdin.on("end", () => process.exit(0));
