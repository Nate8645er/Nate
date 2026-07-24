/**
 * Bildverständnis (Erweiterung, ersetzt nichts) – dependency-frei über die
 * Anthropic-Messages-REST-API (bild-fähiges Modell).
 *
 * Ermöglicht: ein per Kamera aufgenommenes oder hochgeladenes Bild wird
 * beschrieben/ausgewertet (z. B. Beleg, Notiz, Whiteboard, Produktfoto).
 * Aktivierung: ANTHROPIC_API_KEY. Ohne Key ehrlich „nicht-konfiguriert" –
 * kein Schein-Ergebnis. Passt zum bestehenden Provider-Muster (lib/agents).
 */

export type VisionEnv = Record<string, string | undefined>;

export function visionKonfiguriert(env: VisionEnv = process.env): boolean {
  const k = env.ANTHROPIC_API_KEY;
  return typeof k === "string" && k.startsWith("sk-ant");
}

/** Erlaubte Bild-Typen (Anthropic-Vision unterstützt genau diese). */
const ERLAUBTE_TYPEN = new Set(["image/jpeg", "image/png", "image/gif", "image/webp"]);

export interface VisionEingabe {
  /** Base64-Bilddaten OHNE data:-Präfix. */
  base64: string;
  /** MIME-Typ, z. B. image/jpeg. */
  mediaType: string;
  /** Optionale Frage/Anweisung zum Bild. */
  frage?: string;
}

/**
 * Beschreibt/analysiert ein Bild. Reine Netzfunktion mit injizierbarem fetch;
 * gibt Text zurück oder einen ehrlichen Fehlercode (wirft nie).
 */
export async function bildBeschreiben(
  eingabe: VisionEingabe,
  env: VisionEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<
  | { ok: true; text: string }
  | { ok: false; error: "nicht-konfiguriert" | "ungueltige-daten" | "vision-fehler" }
> {
  if (!visionKonfiguriert(env)) return { ok: false, error: "nicht-konfiguriert" };
  if (!eingabe.base64 || !ERLAUBTE_TYPEN.has(eingabe.mediaType)) {
    return { ok: false, error: "ungueltige-daten" };
  }
  const frage =
    (eingabe.frage ?? "").trim().slice(0, 1000) ||
    "Beschreibe dieses Bild sachlich auf Deutsch. Wenn Text zu sehen ist, gib ihn wieder.";

  try {
    const res = await fetchImpl("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "x-api-key": env.ANTHROPIC_API_KEY as string,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: env.VISION_MODEL || "claude-sonnet-5",
        max_tokens: 1024,
        messages: [
          {
            role: "user",
            content: [
              { type: "image", source: { type: "base64", media_type: eingabe.mediaType, data: eingabe.base64 } },
              { type: "text", text: frage },
            ],
          },
        ],
      }),
    });
    if (!res.ok) return { ok: false, error: "vision-fehler" };
    const data = (await res.json()) as { content?: { type: string; text?: string }[] };
    const text = (data.content ?? []).filter((c) => c.type === "text").map((c) => c.text ?? "").join("\n").trim();
    if (!text) return { ok: false, error: "vision-fehler" };
    return { ok: true, text };
  } catch {
    return { ok: false, error: "vision-fehler" };
  }
}

/** Zerlegt eine data:-URL in mediaType + base64 (für den Upload aus dem Browser). */
export function dataUrlZerlegen(dataUrl: string): { mediaType: string; base64: string } | null {
  const m = /^data:([a-z/+.-]+);base64,(.+)$/i.exec(dataUrl.trim());
  if (!m) return null;
  return { mediaType: m[1].toLowerCase(), base64: m[2] };
}
