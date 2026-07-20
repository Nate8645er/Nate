/**
 * POST /api/mission
 *
 * Nimmt { goal: string } entgegen und streamt den Missionsverlauf als
 * Server-Sent-Events (AgentEvent-JSON pro "data:"-Zeile) zurueck.
 *
 * TODO Phase 2: Auth-Check (lib/auth-stub.ts) + Missions-Limit je Plan
 * (lib/billing-stub.ts) vor dem Start der Mission durchsetzen.
 */

import { runMission } from "@/lib/agents/orchestrator";
import type { AgentEvent } from "@/lib/agents/types";

export const runtime = "nodejs";
// Eine Mission umfasst 4 sequenzielle LLM-Phasen – grosszuegig dimensionieren.
export const maxDuration = 300;

const MAX_GOAL_LENGTH = 2000;

export async function POST(request: Request): Promise<Response> {
  let goal: unknown;
  try {
    const body: unknown = await request.json();
    goal = (body as { goal?: unknown })?.goal;
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

      try {
        await runMission(missionGoal, emit);
      } catch (err) {
        emit({
          type: "error",
          agent: null,
          message:
            err instanceof Error ? err.message : "Unbekannter Serverfehler.",
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

function jsonError(message: string, status: number): Response {
  return Response.json({ error: message }, { status });
}
