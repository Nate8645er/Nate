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
  url: string;
  envKey: string;
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
};

/**
 * Prüft, ob für den Provider ein API-Key in process.env hinterlegt ist.
 * Der Orchestrator nutzt das, um ohne Key direkt in den Demo-Modus zu gehen.
 */
export function hasApiKey(provider: Provider): boolean {
  return Boolean(process.env[ENDPOINTS[provider].envKey]?.trim());
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
  const endpoint = ENDPOINTS[provider];
  const apiKey = process.env[endpoint.envKey];

  if (!apiKey) {
    return {
      ok: false,
      error: `${endpoint.envKey} ist nicht gesetzt (.env prüfen).`,
    };
  }
  if (messages.length === 0) {
    return { ok: false, error: "Leere Nachrichtenliste übergeben." };
  }

  const { headers, body } =
    provider === "anthropic"
      ? buildAnthropicRequest(apiKey, model, system, messages)
      : buildOpenAIStyleRequest(apiKey, model, system, messages);

  let lastError = `${provider}: unbekannter Fehler`;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const outcome = await attemptRequest(provider, endpoint.url, headers, body);
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
  const endpoint = ENDPOINTS[provider];
  const apiKey = process.env[endpoint.envKey];
  if (!apiKey) {
    return { ok: false, error: `${endpoint.envKey} ist nicht gesetzt (.env prüfen).` };
  }
  if (messages.length === 0) {
    return { ok: false, error: "Leere Nachrichtenliste übergeben." };
  }

  const { headers, body } =
    provider === "anthropic"
      ? buildAnthropicRequest(apiKey, model, system, messages)
      : buildOpenAIStyleRequest(apiKey, model, system, messages);
  // stream:true aktiviert Server-Sent-Events beim Provider.
  const streamBody = { ...body, stream: true };

  let response: Response;
  try {
    response = await fetch(endpoint.url, {
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
  apiKey: string,
  model: string,
  system: string,
  messages: ChatMessage[],
) {
  return {
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${apiKey}`,
    },
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

/** Liest den Fehlertext einer Nicht-2xx-Antwort, ohne selbst zu werfen. */
async function safeErrorDetail(response: Response): Promise<string> {
  try {
    const text = await response.text();
    return text.slice(0, 300);
  } catch {
    return "(Fehlertext nicht lesbar)";
  }
}
