/**
 * POST /api/extract
 *
 * Nimmt ein PDF als multipart/FormData (Feld "file", max 4 MB) entgegen,
 * extrahiert den Text serverseitig mit pdf-parse und antwortet mit
 * { text, pages }. Wird vom Dashboard für die Dokumenten-Analyse
 * aufgerufen; TXT/MD/CSV/HTML liest der Client selbst per FileReader.
 */

import { PDFParse } from "pdf-parse";

export const runtime = "nodejs";
export const maxDuration = 60;

/** Harte Obergrenze für den PDF-Upload (Vercel-tauglich). */
const MAX_FILE_BYTES = 4 * 1024 * 1024;

export async function POST(request: Request): Promise<Response> {
  let file: File;
  try {
    const form = await request.formData();
    const raw = form.get("file");
    if (!(raw instanceof File)) {
      return jsonError('Formularfeld "file" (PDF-Datei) ist erforderlich.', 400);
    }
    file = raw;
  } catch {
    return jsonError("Ungültiger Request-Body (multipart/form-data erwartet).", 400);
  }

  if (file.size === 0) {
    return jsonError("Die Datei ist leer.", 400);
  }
  if (file.size > MAX_FILE_BYTES) {
    return jsonError("Die Datei darf maximal 4 MB gross sein.", 413);
  }

  const data = new Uint8Array(await file.arrayBuffer());
  // PDF-Magic-Bytes prüfen statt dem Client-MIME-Type zu vertrauen.
  if (!isPdf(data)) {
    return jsonError("Nur PDF-Dateien werden unterstützt.", 415);
  }

  const parser = new PDFParse({ data });
  try {
    // pageJoiner "\n": Seiten nur durch Zeilenumbruch trennen statt der
    // Standard-Markierung "-- 1 of n --" (stört die Dokumenten-Analyse).
    const result = await parser.getText({ pageJoiner: "\n" });
    return Response.json({ text: (result.text ?? "").trim(), pages: result.total ?? 0 });
  } catch (err) {
    // Interne Details nur serverseitig loggen, Client erhält generische Meldung.
    console.error("[extract] PDF-Extraktion fehlgeschlagen:", err);
    return jsonError(
      "Das PDF konnte nicht gelesen werden (beschädigt oder verschlüsselt?).",
      422,
    );
  } finally {
    await parser.destroy().catch(() => { /* bereits freigegeben */ });
  }
}

/** Prüft die "%PDF-"-Signatur am Dateianfang. */
function isPdf(data: Uint8Array): boolean {
  const magic = [0x25, 0x50, 0x44, 0x46, 0x2d]; // "%PDF-"
  return data.length >= magic.length && magic.every((b, i) => data[i] === b);
}

function jsonError(message: string, status: number): Response {
  return Response.json({ error: message }, { status });
}
