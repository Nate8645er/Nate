/**
 * POST /api/mission
 *
 * Nimmt { goal: string, context?: { branche, groesse } } entgegen und
 * streamt den Missionsverlauf als Server-Sent-Events (AgentEvent-JSON
 * pro "data:"-Zeile) zurueck.
 *
 * Plan- und Limit-Durchsetzung (stateless, lib/license.ts):
 * - Header "x-acc-license": signiertes Lizenz-Token (30 Tage). Fehlend,
 *   manipuliert oder abgelaufen => Plan FREE.
 * - Header "x-acc-usage": signiertes Usage-Token (Tageszaehler). Der
 *   Server signiert es bei jeder Antwort neu und sendet es als erstes
 *   SSE-Event { type: "usage", token, used, limit, plan }.
 * - Ueberschrittenes Tageslimit => error-Event statt Mission.
 */

import { runMission } from "@/lib/agents/orchestrator";
import type { AgentEvent, MissionContext } from "@/lib/agents/types";
import { consumeUsage, planFromLicenseToken } from "@/lib/license";

export const runtime = "nodejs";
// Eine Mission umfasst 4 sequenzielle LLM-Phasen – grosszuegig dimensionieren.
export const maxDuration = 300;

const MAX_GOAL_LENGTH = 2000;
const MAX_CONTEXT_FIELD_LENGTH = 80;
/** Serverseitige Kappung des angehaengten Dokuments (Dokumenten-Analyse). */
const MAX_DOKUMENT_NAME_LENGTH = 80;
const MAX_DOKUMENT_TEXT_LENGTH = 20_000;

export async function POST(request: Request): Promise<Response> {
  let goal: unknown;
  let rawContext: unknown;
  try {
    const body: unknown = await request.json();
    goal = (body as { goal?: unknown })?.goal;
    rawContext = (body as { context?: unknown })?.context;
  } catch {
    return jsonError("Ungueltiger Request-Body (JSON erwartet).", 400);
  }

  if (typeof goal !== "string" || !goal.trim()) {
    return jsonError('Feld "goal" (nicht-leerer String) ist erforderlich.', 400);
  }
  if (goal.length > MAX_GOAL_LENGTH) {
    return jsonError(`"goal" darf maximal ${MAX_GOAL_LENGTH} Zeichen lang sein.`, 400);
  }

  const missionGoal = goal.trim();
  const context = sanitizeContext(rawContext);

  // Plan + Tageslimit VOR dem Missionsstart durchsetzen (stateless).
  const plan = planFromLicenseToken(request.headers.get("x-acc-license"));
  const usage = consumeUsage(request.headers.get("x-acc-usage"), plan);

  const encoder = new TextEncoder();

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let closed = false;
      const emit = (event: AgentEvent) => {
        if (closed) return;
        try {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(event)}\n\n`),
          );
        } catch {
          // Client hat die Verbindung geschlossen – weitere Events verwerfen.
          closed = true;
        }
      };

      // Neu signiertes Usage-Token immer zuerst an den Client zurueckgeben.
      emit({
        type: "usage",
        token: usage.token,
        used: usage.used,
        limit: usage.limit,
        plan,
      });

      try {
        if (!usage.allowed) {
          emit({
            type: "error",
            agent: null,
            message: usage.message ?? "Tageslimit erreicht.",
          });
          return;
        }
        // Plan aus dem validierten Lizenz-Token steuert den Agenten-Fan-out.
        await runMission(missionGoal, emit, context, plan);
      } catch (err) {
        emit({
          type: "error",
          agent: null,
          message:
            // Interne Details nur serverseitig loggen, Client erhaelt generische Meldung.
            (console.error("[mission] Serverfehler:", err),
            "Die Mission konnte nicht abgeschlossen werden. Bitte erneut versuchen."),
        });
      } finally {
        if (!closed) {
          try {
            controller.close();
          } catch {
            /* bereits geschlossen */
          }
        }
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}

/** Validiert den optionalen Onboarding-Kontext; unbrauchbares => undefined. */
function sanitizeContext(raw: unknown): MissionContext | undefined {
  if (typeof raw !== "object" || raw === null) return undefined;
  const branche = cleanContextField((raw as { branche?: unknown }).branche);
  const groesse = cleanContextField((raw as { groesse?: unknown }).groesse);
  const dokument = sanitizeDokument((raw as { dokument?: unknown }).dokument);
  const onboarding = branche && groesse ? { branche, groesse } : {};
  if ((!branche || !groesse) && !dokument) return undefined;
  return { ...onboarding, ...(dokument ? { dokument } : {}) };
}

/**
 * Validiert das optionale angehaengte Dokument und kappt serverseitig
 * name (80) und text (20000 Zeichen); unbrauchbares => undefined.
 */
function sanitizeDokument(raw: unknown): MissionContext["dokument"] | undefined {
  if (typeof raw !== "object" || raw === null) return undefined;
  const { name, text } = raw as { name?: unknown; text?: unknown };
  if (typeof name !== "string" || typeof text !== "string") return undefined;
  const cleanName = name.replace(/\s+/g, " ").trim().slice(0, MAX_DOKUMENT_NAME_LENGTH);
  const cleanText = text.slice(0, MAX_DOKUMENT_TEXT_LENGTH).trim();
  if (!cleanName || !cleanText) return undefined;
  return { name: cleanName, text: cleanText };
}

/** Trimmt, entfernt Zeilenumbrueche und begrenzt die Laenge. */
function cleanContextField(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const clean = value.replace(/\s+/g, " ").trim().slice(0, MAX_CONTEXT_FIELD_LENGTH);
  return clean || null;
}

function jsonError(message: string, status: number): Response {
  return Response.json({ error: message }, { status });
}
