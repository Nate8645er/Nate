/**
 * POST /api/bild
 *
 * Nimmt ein Bild (data-URL aus Kamera oder Upload) + optionale Frage entgegen
 * und liefert eine Beschreibung/Auswertung über ein bild-fähiges Modell.
 * Ohne ANTHROPIC_API_KEY ehrlich 501 „nicht-konfiguriert".
 */

import { bildBeschreiben, dataUrlZerlegen } from "@/lib/vision";

export const runtime = "nodejs";
export const maxDuration = 60;

const MAX_BYTES = 6 * 1024 * 1024; // ~6 MB Bild (Anthropic-Limit-nah)

export async function POST(request: Request): Promise<Response> {
  let body: { bild?: unknown; frage?: unknown };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return Response.json({ error: "ungueltiger-body" }, { status: 400 });
  }
  const dataUrl = typeof body.bild === "string" ? body.bild : "";
  const frage = typeof body.frage === "string" ? body.frage : "";
  const zerlegt = dataUrlZerlegen(dataUrl);
  if (!zerlegt) return Response.json({ error: "kein-bild" }, { status: 400 });
  // Grobe Grössenkontrolle (base64 ~4/3 der Bytes).
  if (zerlegt.base64.length * 0.75 > MAX_BYTES) {
    return Response.json({ error: "bild-zu-gross" }, { status: 413 });
  }

  const r = await bildBeschreiben({ base64: zerlegt.base64, mediaType: zerlegt.mediaType, frage });
  if (r.ok) return Response.json({ text: r.text });

  const status = r.error === "nicht-konfiguriert" ? 501 : r.error === "ungueltige-daten" ? 400 : 502;
  return Response.json({ error: r.error }, { status });
}
