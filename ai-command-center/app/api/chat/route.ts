/**
 * POST /api/chat
 *
 * KI-Chat für Mitarbeitende: nimmt { messages, context? } entgegen und
 * antwortet als JSON { ok, text, usage }. Kein Streaming nötig – eine
 * Antwort ist ein einzelner LLM-Aufruf mit Timeout + Fallback-Kette.
 *
 * Plan-/Limit-Durchsetzung wie bei /api/mission (stateless):
 * - "x-acc-license": signiertes Lizenz-Token; fehlend/ungültig => FREE.
 * - "x-acc-usage":   signiertes Usage-Token; jede Chat-Antwort zählt
 *   wie eine Mission auf das Tageslimit.
 *
 * Fallback-Kette: Anthropic -> OpenAI -> Moonshot -> Demo-Antwort.
 * Der Chat hängt damit nie: ohne Keys antwortet der Demo-Modus ehrlich.
 */

import { hasApiKey, callLLM } from "@/lib/agents/providers";
import type { ChatMessage, Provider } from "@/lib/agents/types";
import { consumeUsage, planFromLicenseToken } from "@/lib/license";

export const runtime = "nodejs";
export const maxDuration = 120;

const MAX_MESSAGES = 30;
const MAX_MESSAGE_LENGTH = 8_000;

/** Reihenfolge der Provider-Fallbacks samt Modell. */
const CHAT_CHAIN: { provider: Provider; model: string }[] = [
  { provider: "anthropic", model: "claude-sonnet-5" },
  { provider: "openai", model: "gpt-4o-mini" },
  { provider: "moonshot", model: "kimi-k3" },
];

function systemPrompt(branche?: string, groesse?: string): string {
  const kontext =
    branche && groesse
      ? `\nUnternehmenskontext des Nutzers: Branche ${branche}, Grösse ${groesse}. Beziehe dich darauf, wenn es hilft.`
      : "";
  return (
    "Du bist der KI-Assistent des AI Command Center – der digitalen " +
    "KI-Belegschaft für Unternehmen. Du hilfst Mitarbeitenden schnell und " +
    "konkret bei Geschäftsfragen: Texte, Ideen, Analysen, E-Mails, Planung, " +
    "Erklärungen. Antworte auf Deutsch (Schweizer Schreibweise, kein ß), " +
    "siezen Sie den Nutzer konsequent, präzise und ohne Fülltext. " +
    "Nutze Markdown sparsam (Listen, **fett**). " +
    "Wenn eine Aufgabe ein grosses fertiges Ergebnis braucht (Website, " +
    "Dokument, Präsentation), empfiehl dafür eine Mission im Dashboard." +
    kontext
  );
}

export async function POST(request: Request): Promise<Response> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ ok: false, error: "Ungültiger Request-Body." }, { status: 400 });
  }

  const messages = sanitizeMessages((body as { messages?: unknown })?.messages);
  if (!messages) {
    return Response.json(
      { ok: false, error: 'Feld "messages" (nicht-leere Liste) ist erforderlich.' },
      { status: 400 },
    );
  }
  const branche = cleanField((body as { context?: { branche?: unknown } })?.context?.branche);
  const groesse = cleanField((body as { context?: { groesse?: unknown } })?.context?.groesse);

  const plan = planFromLicenseToken(request.headers.get("x-acc-license"));
  const usage = consumeUsage(request.headers.get("x-acc-usage"), plan);
  const usagePayload = {
    token: usage.token,
    used: usage.used,
    limit: usage.limit,
    plan,
  };

  if (!usage.allowed) {
    return Response.json({
      ok: false,
      error: usage.message ?? "Tageslimit erreicht.",
      usage: usagePayload,
    });
  }

  const system = systemPrompt(branche ?? undefined, groesse ?? undefined);

  for (const step of CHAT_CHAIN) {
    if (!hasApiKey(step.provider)) continue;
    const result = await callLLM(step.provider, step.model, system, messages);
    if (result.ok) {
      return Response.json({ ok: true, text: result.text, usage: usagePayload });
    }
    console.error(`[chat] ${step.provider} fehlgeschlagen:`, result.error);
  }

  // Demo-Modus: ehrlich gekennzeichnete Antwort ohne LLM.
  return Response.json({
    ok: true,
    text:
      "**Demo-Modus:** Es ist gerade kein KI-Anbieter erreichbar, darum " +
      "antworte ich mit einer Beispiel-Antwort.\n\nIhre Frage ist angekommen: " +
      `«${messages[messages.length - 1].content.slice(0, 160)}»\n\n` +
      "Im Vollbetrieb erhalten Sie hier eine fundierte Antwort Ihres " +
      "KI-Assistenten – zugeschnitten auf Ihre Branche. Für fertige " +
      "Ergebnisse (Website, Dokument, Präsentation) starten Sie eine " +
      "Mission im Dashboard.",
    usage: usagePayload,
  });
}

/** Validiert und kappt die Chat-Historie; unbrauchbares => null. */
function sanitizeMessages(raw: unknown): ChatMessage[] | null {
  if (!Array.isArray(raw) || raw.length === 0) return null;
  const cleaned: ChatMessage[] = [];
  for (const item of raw.slice(-MAX_MESSAGES)) {
    const role = (item as { role?: unknown })?.role;
    const content = (item as { content?: unknown })?.content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") {
      return null;
    }
    const text = content.trim().slice(0, MAX_MESSAGE_LENGTH);
    if (!text) return null;
    cleaned.push({ role, content: text });
  }
  // Konversation muss mit einer Nutzer-Nachricht enden.
  if (cleaned.length === 0 || cleaned[cleaned.length - 1].role !== "user") return null;
  return cleaned;
}

function cleanField(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const clean = value.replace(/\s+/g, " ").trim().slice(0, 80);
  return clean || null;
}
