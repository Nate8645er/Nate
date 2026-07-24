/**
 * Provider-agnostischer LLM-Client.
 *
 * Ein einziger Einstiegspunkt (callLLM) kapselt die drei Anbieter:
 *  - anthropic  -> Messages API (api.anthropic.com/v1/messages)
 *  - openai     -> Chat Completions (api.openai.com/v1/chat/completions)
 *  - moonshot   -> Chat Completions im OpenAI-Format (api.moonshot.ai)
 *
 * Fehler werden nie geworfen, sondern als { ok: false, error } zurückgegeben,
 * damit der Orchestrator pro Agent sauber degradieren kann.
 */

import { AsyncLocalStorage } from "node:async_hooks";
import type { ChatMessage, LLMResult, Provider } from "./types";

const REQUEST_TIMEOUT_MS = 90_000;
const MAX_TOKENS = 4096;

/**
 * Token-Budget der laufenden Mission (max_tokens je Antwort, plan-abhängig).
 * Wird vom Orchestrator per run() um die Mission gelegt – AsyncLocalStorage
 * hält das Budget pro Request getrennt, auch bei parallelen Missionen.
 */
export const tokenBudgetStore = new AsyncLocalStorage<number>();

/** Aktives max_tokens: Mission-Budget, sonst Obergrenze. */
function aktivesMaxTokens(): number {
  const budget = tokenBudgetStore.getStore();
  return budget && budget > 0 ? Math.min(budget, MAX_TOKENS) : MAX_TOKENS;
}
/** Ein Wiederholungsversuch bei Netz-/5xx-Fehlern. */
const MAX_ATTEMPTS = 2;

interface ProviderEndpoint {
  /** Statische Standard-URL (leer = muss per <urlEnv> gesetzt werden). */
  url: string;
  /** Env-Variable mit dem API-Key (Bearer/x-api-key). */
  envKey: string;
  /** Optionale Env-Variable, um die Endpoint-URL zu überschreiben. */
  urlEnv?: string;
  /** true = ohne API-Key nutzbar (selbst gehostet), Key nur optional. */
  keyOptional?: boolean;
}

const ENDPOINTS: Record<Provider, ProviderEndpoint> = {
  anthropic: {
    url: "https://api.anthropic.com/v1/messages",
    envKey: "ANTHROPIC_API_KEY",
  },
  openai: {
    url: "https://api.openai.com/v1/chat/completions",
    envKey: "OPENAI_API_KEY",
  },
  moonshot: {
    url: "https://api.moonshot.ai/v1/chat/completions",
    envKey: "MOONSHOT_API_KEY",
  },
  // Lokales/eigenes Modell (OpenAI-kompatibel). URL kommt aus der Umgebung,
  // damit jede Firma ihr eigenes Modell (Ollama/vLLM/LM Studio) anbinden kann.
  local: {
    url: "",
    envKey: "LOCAL_LLM_API_KEY",
    urlEnv: "LOCAL_LLM_URL",
    keyOptional: true,
  },
  // Frontier-Anbieter des Modell-Rats – alle OpenAI-kompatibel. Standard-URL
  // vorbelegt, per <PROVIDER>_LLM_URL überschreibbar (z. B. eigener Proxy/Host).
  google: {
    url: "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    envKey: "GOOGLE_API_KEY",
    urlEnv: "GOOGLE_LLM_URL",
  },
  xai: {
    url: "https://api.x.ai/v1/chat/completions",
    envKey: "XAI_API_KEY",
    urlEnv: "XAI_LLM_URL",
  },
  qwen: {
    url: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
    envKey: "QWEN_API_KEY",
    urlEnv: "QWEN_LLM_URL",
  },
  deepseek: {
    url: "https://api.deepseek.com/v1/chat/completions",
    envKey: "DEEPSEEK_API_KEY",
    urlEnv: "DEEPSEEK_LLM_URL",
  },
  // Meta Llama hat keine erste-Partei-API: URL eines OpenAI-kompatiblen Hosts
  // (Together/Fireworks/Groq/eigener vLLM) per META_LLM_URL setzen.
  meta: {
    url: "",
    envKey: "META_API_KEY",
    urlEnv: "META_LLM_URL",
    keyOptional: true,
  },
  mistral: {
    url: "https://api.mistral.ai/v1/chat/completions",
    envKey: "MISTRAL_API_KEY",
    urlEnv: "MISTRAL_LLM_URL",
  },
};

/** Effektive Endpoint-URL: Env-Override (falls definiert) vor der Standard-URL. */
function endpointUrl(provider: Provider): string {
  const ep = ENDPOINTS[provider];
  if (ep.urlEnv) {
    const override = process.env[ep.urlEnv]?.trim();
    if (override) return override;
  }
  return ep.url;
}

/**
 * Auth-Schlüssel für den Bearer/x-api-key-Header. Bei selbst gehosteten
 * Providern (local/meta) ist er optional – dann kein Authorization-Header.
 */
function authKey(provider: Provider): string | undefined {
  return process.env[ENDPOINTS[provider].envKey]?.trim() || undefined;
}

/**
 * Effektive Modell-ID: per <PROVIDER>_MODEL überschreibbar, sonst der Standard
 * aus dem Modell-Rat/der Team-Konfiguration.
 */
export function modelId(provider: Provider, fallback: string): string {
  const key = provider === "local" ? "LOCAL_LLM_MODEL" : `${provider.toUpperCase()}_MODEL`;
  return process.env[key]?.trim() || fallback;
}

/**
 * Ist der Provider einsatzbereit? Cloud: API-Key gesetzt. Selbst gehostet
 * (local/meta): URL gesetzt (Key optional). Der Orchestrator und die
 * Modell-Rat-Übersicht nutzen das, um nicht konfigurierte Modelle zu
 * überspringen bzw. ehrlich als „nicht konfiguriert" zu markieren.
 */
export function hasApiKey(provider: Provider): boolean {
  const ep = ENDPOINTS[provider];
  if (ep.keyOptional) return Boolean(endpointUrl(provider));
  return Boolean(authKey(provider)) && Boolean(endpointUrl(provider));
}

/**
 * Bevorzugte Reihenfolge für den EIN-KEY-BETRIEB: Der Betreiber hinterlegt
 * nur EINEN Provider-Key (z. B. ANTHROPIC_API_KEY in Vercel), und das ganze
 * Team arbeitet echt darüber – der Kunde braucht nie einen eigenen Key. Ist
 * ein von einem Agenten gewünschter Provider nicht konfiguriert, wird auf den
 * ersten hier gelisteten konfigurierten Provider umgeleitet.
 */
const FALLBACK_ORDER: readonly Provider[] = [
  "anthropic",
  "openai",
  "moonshot",
  "google",
  "xai",
  "deepseek",
  "mistral",
  "qwen",
  "meta",
  "local",
];

/** Standard-Modell je Provider, wenn ein Agent dorthin umgeleitet wird. */
const FALLBACK_MODEL: Record<Provider, string> = {
  anthropic: "claude-sonnet-5",
  openai: "gpt-4o-mini",
  moonshot: "kimi-k3",
  google: "gemini-2.5-flash",
  xai: "grok-4",
  deepseek: "deepseek-chat",
  mistral: "mistral-large-latest",
  qwen: "qwen-max",
  meta: "llama-3.3-70b",
  local: "local-model",
};

/** Erster konfigurierter Provider (Key/URL vorhanden) in Präferenzreihenfolge. */
export function firstConfiguredProvider(): Provider | null {
  for (const p of FALLBACK_ORDER) {
    if (hasApiKey(p)) return p;
  }
  return null;
}

/**
 * Löst (provider, model) für einen Agenten auf.
 *
 * - Hat der gewünschte Provider einen Key, bleibt alles unverändert (volle
 *   Modell-Vielfalt, wenn der Betreiber mehrere Keys hinterlegt).
 * - Sonst wird auf den ersten konfigurierten Provider umgeleitet und dessen
 *   Standard-Modell (per <PROVIDER>_MODEL überschreibbar) genutzt. So genügt
 *   EIN Key (z. B. Anthropic), damit das gesamte Team echt arbeitet.
 * - Ist gar kein Provider konfiguriert, gibt es null zurück → der Orchestrator
 *   greift dann sauber auf den Demo-Fallback zurück.
 */
export function resolveProviderModel(
  provider: Provider,
  model: string,
): { provider: Provider; model: string } | null {
  if (hasApiKey(provider)) return { provider, model };
  const fallback = firstConfiguredProvider();
  if (!fallback) return null;
  return { provider: fallback, model: modelId(fallback, FALLBACK_MODEL[fallback]) };
}

/**
 * Ruft das angegebene Modell beim jeweiligen Provider auf.
 *
 * Netz-/Timeout-Fehler und HTTP 5xx werden genau einmal wiederholt;
 * 4xx-Fehler (falscher Key, ungültiges Modell) sofort zurückgegeben.
 *
 * @param provider  anthropic | openai | moonshot
 * @param model     Modell-ID, z. B. "claude-sonnet-5" oder "gpt-4o-mini"
 * @param system    System-Prompt (deutsch)
 * @param messages  Konversation im providerneutralen Format
 */
export async function callLLM(
  provider: Provider,
  model: string,
  system: string,
  messages: ChatMessage[],
): Promise<LLMResult> {
  const url = endpointUrl(provider);
  if (!url) {
    return { ok: false, error: nichtKonfiguriert(provider) };
  }
  const apiKey = authKey(provider);
  // Cloud-Provider brauchen zwingend einen Key; local/meta ist er optional.
  if (!ENDPOINTS[provider].keyOptional && !apiKey) {
    return { ok: false, error: nichtKonfiguriert(provider) };
  }
  if (messages.length === 0) {
    return { ok: false, error: "Leere Nachrichtenliste übergeben." };
  }

  const { headers, body } =
    provider === "anthropic"
      ? buildAnthropicRequest(apiKey ?? "", model, system, messages)
      : buildOpenAIStyleRequest(apiKey, model, system, messages);

  let lastError = `${provider}: unbekannter Fehler`;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const outcome = await attemptRequest(provider, url, headers, body);
    if (outcome.ok) return { ok: true, text: outcome.text };
    lastError = outcome.error;
    if (!outcome.retryable) break;
  }
  return { ok: false, error: lastError };
}

type AttemptOutcome =
  | { ok: true; text: string }
  | { ok: false; error: string; retryable: boolean };

/** Ein einzelner HTTP-Versuch; meldet, ob ein Retry sinnvoll ist. */
async function attemptRequest(
  provider: Provider,
  url: string,
  headers: Record<string, string>,
  body: unknown,
): Promise<AttemptOutcome> {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    if (!response.ok) {
      const detail = await safeErrorDetail(response);
      return {
        ok: false,
        error: `${provider} antwortete mit HTTP ${response.status}: ${detail}`,
        // Nur Server-Fehler wiederholen; 4xx ändert ein Retry nicht.
        retryable: response.status >= 500,
      };
    }

    const data: unknown = await response.json();
    const text =
      provider === "anthropic"
        ? extractAnthropicText(data)
        : extractOpenAIStyleText(data);

    if (text === null) {
      return {
        ok: false,
        error: `${provider}: Antwort enthielt keinen Text (unerwartetes Format).`,
        retryable: false,
      };
    }
    return { ok: true, text };
  } catch (err) {
    const reason =
      err instanceof Error && err.name === "TimeoutError"
        ? `Timeout nach ${REQUEST_TIMEOUT_MS / 1000}s`
        : err instanceof Error
          ? err.message
          : String(err);
    return {
      ok: false,
      error: `${provider}: Netzwerkfehler (${reason})`,
      retryable: true,
    };
  }
}

function buildAnthropicRequest(
  apiKey: string,
  model: string,
  system: string,
  messages: ChatMessage[],
) {
  return {
    headers: {
      "content-type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    // Hinweis: keine temperature/top_p senden – aktuelle Claude-Modelle
    // (Sonnet 5) lehnen Sampling-Parameter mit HTTP 400 ab.
    body: {
      model,
      max_tokens: aktivesMaxTokens(),
      system,
      messages,
    },
  };
}

/**
 * Streamt eine LLM-Antwort Token für Token (wie ChatGPT/Claude).
 *
 * Ruft `onDelta` für jedes Text-Fragment auf und gibt am Ende den
 * vollständigen Text zurück – oder einen Fehler, ohne zu werfen.
 * Unterstützt Anthropic (SSE content_block_delta) und OpenAI/Moonshot
 * (SSE choices[].delta.content). Bei Netz-/5xx-Fehlern KEIN Retry, weil
 * bereits Teil-Tokens gesendet worden sein könnten – der Aufrufer fällt
 * dann auf den nächsten Provider zurück, solange noch nichts geflossen ist.
 */
export async function streamLLM(
  provider: Provider,
  model: string,
  system: string,
  messages: ChatMessage[],
  onDelta: (text: string) => void,
): Promise<LLMResult> {
  const url = endpointUrl(provider);
  if (!url) {
    return { ok: false, error: nichtKonfiguriert(provider) };
  }
  const apiKey = authKey(provider);
  if (!ENDPOINTS[provider].keyOptional && !apiKey) {
    return { ok: false, error: nichtKonfiguriert(provider) };
  }
  if (messages.length === 0) {
    return { ok: false, error: "Leere Nachrichtenliste übergeben." };
  }

  const { headers, body } =
    provider === "anthropic"
      ? buildAnthropicRequest(apiKey ?? "", model, system, messages)
      : buildOpenAIStyleRequest(apiKey, model, system, messages);
  // stream:true aktiviert Server-Sent-Events beim Provider.
  const streamBody = { ...body, stream: true };

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(streamBody),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    const reason =
      err instanceof Error && err.name === "TimeoutError"
        ? `Timeout nach ${REQUEST_TIMEOUT_MS / 1000}s`
        : err instanceof Error
          ? err.message
          : String(err);
    return { ok: false, error: `${provider}: Netzwerkfehler (${reason})` };
  }

  if (!response.ok || !response.body) {
    const detail = await safeErrorDetail(response);
    return { ok: false, error: `${provider} antwortete mit HTTP ${response.status}: ${detail}` };
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let full = "";

  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      // SSE: Events sind durch Leerzeilen getrennt; Zeilen beginnen mit "data:".
      let nl: number;
      while ((nl = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, nl).trim();
        buffer = buffer.slice(nl + 1);
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        let json: unknown;
        try {
          json = JSON.parse(payload);
        } catch {
          continue; // unvollständiges/nicht-JSON-Event überspringen
        }
        const delta =
          provider === "anthropic"
            ? extractAnthropicDelta(json)
            : extractOpenAIStyleDelta(json);
        if (delta) {
          full += delta;
          onDelta(delta);
        }
      }
    }
  } catch (err) {
    // Verbindung mitten im Stream abgebrochen: was da ist, ist gültig.
    if (full) return { ok: true, text: full };
    return {
      ok: false,
      error: `${provider}: Stream abgebrochen (${err instanceof Error ? err.message : String(err)})`,
    };
  }

  return full.length > 0
    ? { ok: true, text: full }
    : { ok: false, error: `${provider}: leerer Stream.` };
}

/** Text-Delta aus einem Anthropic-SSE-Event (content_block_delta). */
function extractAnthropicDelta(data: unknown): string | null {
  if (typeof data !== "object" || data === null) return null;
  const d = data as { type?: unknown; delta?: { type?: unknown; text?: unknown } };
  if (d.type === "content_block_delta" && d.delta?.type === "text_delta" && typeof d.delta.text === "string") {
    return d.delta.text;
  }
  return null;
}

/** Text-Delta aus einem OpenAI-/Moonshot-SSE-Event (choices[].delta.content). */
function extractOpenAIStyleDelta(data: unknown): string | null {
  if (typeof data !== "object" || data === null) return null;
  const choices = (data as { choices?: unknown }).choices;
  if (!Array.isArray(choices) || choices.length === 0) return null;
  const content = (choices[0] as { delta?: { content?: unknown } }).delta?.content;
  return typeof content === "string" && content.length > 0 ? content : null;
}

function buildOpenAIStyleRequest(
  apiKey: string | undefined,
  model: string,
  system: string,
  messages: ChatMessage[],
) {
  // Authorization nur senden, wenn ein Key vorhanden ist – lokale Server
  // (Ollama/vLLM) laufen oft ohne Auth.
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (apiKey) headers.authorization = `Bearer ${apiKey}`;
  return {
    headers,
    body: {
      model,
      max_tokens: aktivesMaxTokens(),
      messages: [{ role: "system", content: system }, ...messages],
    },
  };
}

/** Extrahiert Text aus einer Anthropic-Messages-Antwort. */
function extractAnthropicText(data: unknown): string | null {
  if (typeof data !== "object" || data === null) return null;
  const content = (data as { content?: unknown }).content;
  if (!Array.isArray(content)) return null;
  const text = content
    .filter(
      (block): block is { type: string; text: string } =>
        typeof block === "object" &&
        block !== null &&
        (block as { type?: unknown }).type === "text" &&
        typeof (block as { text?: unknown }).text === "string",
    )
    .map((block) => block.text)
    .join("");
  return text.length > 0 ? text : null;
}

/** Extrahiert Text aus einer OpenAI-/Moonshot-Chat-Completions-Antwort. */
function extractOpenAIStyleText(data: unknown): string | null {
  if (typeof data !== "object" || data === null) return null;
  const choices = (data as { choices?: unknown }).choices;
  if (!Array.isArray(choices) || choices.length === 0) return null;
  const message = (choices[0] as { message?: { content?: unknown } }).message;
  return typeof message?.content === "string" && message.content.length > 0
    ? message.content
    : null;
}

/** Klartext-Hinweis, welche Env-Variable(n) für den Provider fehlen. */
function nichtKonfiguriert(provider: Provider): string {
  const ep = ENDPOINTS[provider];
  if (ep.keyOptional) {
    return `${ep.urlEnv ?? ep.envKey} ist nicht gesetzt – ${provider}-Modell nicht konfiguriert (.env prüfen).`;
  }
  return `${ep.envKey} ist nicht gesetzt – ${provider}-Modell nicht konfiguriert (.env prüfen).`;
}

/** Liest den Fehlertext einer Nicht-2xx-Antwort, ohne selbst zu werfen. */
async function safeErrorDetail(response: Response): Promise<string> {
  try {
    const text = await response.text();
    return text.slice(0, 300);
  } catch {
    return "(Fehlertext nicht lesbar)";
  }
}
