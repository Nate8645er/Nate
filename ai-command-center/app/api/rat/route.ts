/**
 * POST /api/rat  – der Modell-Rat live.
 *
 * Nimmt { question } entgegen und lässt mehrere Frontier-Modelle dieselbe
 * Frage parallel beantworten; danach führt der Boss (Fable 5) ihre Antworten
 * zu EINER Gesamtantwort zusammen – gestreamt als Server-Sent-Events.
 *
 * Ablauf:
 *  1. Aktive Worker (Key/URL gesetzt) bekommen die Frage parallel.
 *     Pro Worker: {type:"worker-start"} und danach {type:"worker-done"}.
 *  2. Boss-Synthese wird Token für Token gestreamt ({type:"delta"}).
 *  3. Abschluss: {type:"usage"} (Tageszähler) und {type:"done"}.
 *
 * Ehrlich: Sind keine Modelle konfiguriert, antwortet der Endpoint im
 * klar gekennzeichneten Demo-Modus statt etwas vorzutäuschen.
 */

import { callLLM, streamLLM } from "@/lib/agents/providers";
import { ratStatus, RAT_BOSS, type RatModellStatus } from "@/lib/agents/council";
import type { ChatMessage } from "@/lib/agents/types";
import { consumeUsage, planFromLicenseToken, ultraAktiv } from "@/lib/license";

export const runtime = "nodejs";
export const maxDuration = 120;

/** Höchstzahl parallel befragter Worker (Kosten/Laufzeit begrenzen). */
const MAX_WORKER = 6;
const MAX_FRAGE_LEN = 4_000;

function workerSystem(m: RatModellStatus): string {
  return [
    `Du bist ${m.label} (${m.hersteller}), Mitglied im Modell-Rat des AI Command Center.`,
    `Deine Stärke: ${m.rolle}`,
    "Beantworte die Frage des Nutzers direkt, fundiert und kompakt auf Deutsch.",
    "Kennzeichne Annahmen als Annahmen. Keine Rückfragen, liefere ein fertiges Ergebnis.",
  ].join("\n");
}

const BOSS_SYSTEM = [
  "Du bist Fable 5, der Boss und Orchestrator des Modell-Rats.",
  "Mehrere führende KI-Modelle haben dieselbe Frage unabhängig beantwortet.",
  "Führe ihre Antworten zu EINER bestmöglichen Gesamtantwort zusammen:",
  "nutze Übereinstimmungen als starke Aussagen, kläre Widersprüche offen,",
  "ergänze Lücken und verwirf Schwaches. Nenne am Ende kurz in einer Zeile,",
  "worin sich die Modelle einig bzw. uneinig waren.",
  "Antworte auf Deutsch als sauber strukturiertes Markdown.",
].join("\n");

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Ungültiger Request-Body." }, { status: 400 });
  }
  const frage = typeof (body as { question?: unknown })?.question === "string"
    ? (body as { question: string }).question.trim().slice(0, MAX_FRAGE_LEN)
    : "";
  if (!frage) {
    return Response.json({ error: "Bitte eine Frage übergeben." }, { status: 400 });
  }

  const plan = planFromLicenseToken(request.headers.get("x-acc-license"));
  const ultra = ultraAktiv(request.headers.get("x-acc-ultra"), plan);
  const usage = consumeUsage(request.headers.get("x-acc-usage"), plan, ultra);
  const usagePayload = { token: usage.token, used: usage.used, limit: usage.limit, plan };

  // Aktive Worker (ohne Boss), gedeckelt. Boss synthetisiert, wenn aktiv –
  // sonst übernimmt das erste aktive Modell die Synthese.
  const alle = ratStatus();
  const workers = alle.filter((m) => m.aktiv && !m.boss).slice(0, MAX_WORKER);
  const bossStatus = alle.find((m) => m.boss);
  const synth = bossStatus?.aktiv
    ? bossStatus
    : alle.find((m) => m.aktiv) ?? null;

  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      let closed = false;
      const emit = (event: Record<string, unknown>) => {
        if (closed) return;
        try {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
        } catch {
          closed = true;
        }
      };

      try {
        if (!usage.allowed) {
          emit({ type: "error", message: usage.message ?? "Tageslimit erreicht.", usage: usagePayload });
          return;
        }

        // Kein konfiguriertes Modell → ehrlicher Demo-Modus.
        if (!synth || workers.length === 0) {
          emit({
            type: "delta",
            text:
              "**Demo-Modus:** Es sind noch keine (bzw. zu wenige) Rat-Modelle " +
              "konfiguriert. Sobald mindestens ein Worker und der Boss einen " +
              "Zugang haben, befragt der Modell-Rat hier mehrere KI-Modelle " +
              "parallel und führt ihre Antworten zusammen.",
          });
          emit({ type: "usage", ...usagePayload });
          emit({ type: "done" });
          return;
        }

        emit({ type: "roster", boss: { label: synth.label, hersteller: synth.hersteller }, workers: workers.map((w) => ({ id: w.id, label: w.label, hersteller: w.hersteller })) });

        // Alle Worker parallel befragen.
        const frageMsg: ChatMessage[] = [{ role: "user", content: frage }];
        for (const w of workers) emit({ type: "worker-start", id: w.id });
        const ergebnisse = await Promise.all(
          workers.map(async (w) => {
            const r = await callLLM(w.provider, w.effektivesModell, workerSystem(w), frageMsg);
            if (r.ok) {
              emit({ type: "worker-done", id: w.id, ok: true, text: r.text });
              return { label: w.label, hersteller: w.hersteller, text: r.text };
            }
            emit({ type: "worker-done", id: w.id, ok: false, error: kurz(r.error) });
            return null;
          }),
        );
        const gute = ergebnisse.filter((e): e is { label: string; hersteller: string; text: string } => e !== null);

        if (gute.length === 0) {
          emit({ type: "delta", text: "Kein Worker-Modell hat geantwortet (Zugänge/Netz prüfen)." });
          emit({ type: "usage", ...usagePayload });
          emit({ type: "done" });
          return;
        }

        // Boss-Synthese streamen.
        emit({ type: "synth-start", label: synth.label });
        const synthInput =
          `Frage des Nutzers:\n${frage}\n\n` +
          `Antworten der ${gute.length} Modell-Worker:\n\n` +
          gute.map((g) => `=== ${g.label} (${g.hersteller}) ===\n${g.text}`).join("\n\n") +
          "\n\nFühre diese Antworten jetzt zur besten Gesamtantwort zusammen.";
        let streamed = false;
        const res = await streamLLM(synth.provider, synth.effektivesModell, BOSS_SYSTEM, [{ role: "user", content: synthInput }], (delta) => {
          streamed = true;
          emit({ type: "delta", text: delta });
        });
        if (!res.ok && !streamed) {
          // Synthese fehlgeschlagen → Worker-Antworten roh ausgeben, statt nichts.
          emit({ type: "delta", text: gute.map((g) => `### ${g.label}\n${g.text}`).join("\n\n") });
        }

        emit({ type: "usage", ...usagePayload });
        emit({ type: "done" });
      } catch (err) {
        console.error("[rat] Serverfehler:", err);
        emit({ type: "error", message: "Der Modell-Rat konnte nicht abschliessen. Bitte erneut versuchen.", usage: usagePayload });
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

/** Fehlermeldung für die Anzeige kürzen. */
function kurz(msg: string): string {
  return msg.length > 120 ? msg.slice(0, 120) + "…" : msg;
}
