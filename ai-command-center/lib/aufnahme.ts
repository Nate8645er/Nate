/**
 * Kleine, reine Helfer für Medien-Aufnahme (Video/Audio) im Browser.
 * Ausgelagert, damit die Logik ohne DOM testbar ist.
 */

/**
 * Wählt aus einer Prioritätsliste den ersten vom Browser unterstützten
 * MIME-Typ (via Prüf-Funktion, z. B. MediaRecorder.isTypeSupported).
 * Gibt "" zurück, wenn keiner unterstützt wird (Browser wählt dann selbst).
 */
export function waehleMimeTyp(
  kandidaten: readonly string[],
  unterstuetzt: (typ: string) => boolean,
): string {
  for (const typ of kandidaten) {
    try {
      if (unterstuetzt(typ)) return typ;
    } catch {
      /* Prüf-Funktion nicht verfügbar → nächster */
    }
  }
  return "";
}

/** Standard-Prioritäten für Video- bzw. Audio-Aufnahmen. */
export const VIDEO_MIME_KANDIDATEN = [
  "video/webm;codecs=vp9,opus",
  "video/webm;codecs=vp8,opus",
  "video/webm",
  "video/mp4",
] as const;

export const AUDIO_MIME_KANDIDATEN = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
] as const;

/** Sekunden als mm:ss formatieren (für die Aufnahme-Dauer). */
export function dauerFormatieren(sekunden: number): string {
  const s = Math.max(0, Math.floor(sekunden));
  const m = Math.floor(s / 60);
  const rest = s % 60;
  return `${m}:${rest.toString().padStart(2, "0")}`;
}

/** Dateiendung passend zum MIME-Typ (für den Download). */
export function endungFuer(mime: string): string {
  if (mime.includes("mp4")) return "mp4";
  if (mime.startsWith("audio/ogg")) return "ogg";
  if (mime.startsWith("audio")) return "webm";
  return "webm";
}
