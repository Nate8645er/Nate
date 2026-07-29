/**
 * Zuverlässigkeits-Schicht (Erweiterung, ersetzt nichts).
 *
 * LLMs liefern strukturierte Ausgaben oft leicht defekt: in ```json-Blöcken,
 * mit Fliesstext davor/danach, mit typografischen Anführungszeichen oder
 * abschliessenden Kommas. Diese reinen, testbaren Helfer machen das Parsen und
 * die Ausführung robuster – ohne bestehende Logik zu ersetzen.
 *
 * - jsonReparieren: extrahiert das erste balancierte JSON-Objekt/-Array und
 *   repariert häufige Defekte; gibt bei Erfolg das geparste Objekt zurück, sonst
 *   null (nie werfen).
 * - mitWiederholung: Retry mit exponentiellem Backoff (injizierbarer Sleep für
 *   Tests) – für flüchtige Fehler (Netzwerk/Rate-Limit).
 * - backoffPlan / sichereZahl: deterministische Helfer.
 */

/** Findet die erste balancierte {…}- oder […]-Sequenz (String-/Escape-bewusst). */
function ersteBalancierteStruktur(text: string): string | null {
  const start = text.search(/[{[]/);
  if (start < 0) return null;
  const open = text[start];
  const close = open === "{" ? "}" : "]";
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') inStr = false;
    } else if (c === '"') {
      inStr = true;
    } else if (c === open) {
      depth++;
    } else if (c === close) {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

/**
 * Versucht, aus einer (evtl. verrauschten) LLM-Antwort ein JSON-Objekt zu lesen.
 * Gibt das geparste Objekt zurück oder null. Wirft nie.
 */
export function jsonReparieren<T = unknown>(text: string): T | null {
  if (typeof text !== "string" || !text.trim()) return null;

  // 1. ```json … ``` / ``` … ```-Zäune entfernen.
  let roh = text.replace(/```(?:json)?\s*([\s\S]*?)```/gi, "$1");

  // 2. Erste balancierte Struktur herausschneiden (entfernt Prosa davor/danach).
  roh = ersteBalancierteStruktur(roh) ?? roh.trim();

  // 3. Direkt versuchen.
  const versuch = (s: string): T | null => {
    try {
      return JSON.parse(s) as T;
    } catch {
      return null;
    }
  };
  let out = versuch(roh);
  if (out !== null) return out;

  // 4. Leichte Reparaturen und erneut versuchen.
  const repariert = roh
    // typografische Anführungszeichen → gerade
    .replace(/[“”„‟]/g, '"')
    .replace(/[‘’‚‛]/g, "'")
    // abschliessende Kommas vor } oder ]
    .replace(/,\s*([}\]])/g, "$1");
  out = versuch(repariert);
  return out;
}

/** Sichere Zahl mit Fallback (akzeptiert Zahl oder numerischen String). */
export function sichereZahl(wert: unknown, fallback = 0): number {
  if (typeof wert === "number" && Number.isFinite(wert)) return wert;
  if (typeof wert === "string") {
    const n = Number(wert.replace(/[^\d.\-]/g, ""));
    if (Number.isFinite(n)) return n;
  }
  return fallback;
}

/**
 * Deterministische Backoff-Verzögerungen (ms) für `anzahl` Wiederholungen:
 * basisMs * faktor^i, gedeckelt auf maxMs.
 */
export function backoffPlan(anzahl: number, basisMs = 300, faktor = 2, maxMs = 8000): number[] {
  const plan: number[] = [];
  for (let i = 0; i < Math.max(0, anzahl); i++) {
    plan.push(Math.min(maxMs, Math.round(basisMs * Math.pow(faktor, i))));
  }
  return plan;
}

export interface WiederholungsOptionen<T> {
  /** Maximale Gesamtversuche (inkl. Erstversuch). Standard 3. */
  versuche?: number;
  /** Entscheidet, ob bei diesem Fehler erneut versucht wird. Standard: immer. */
  sollWiederholen?: (fehler: unknown, versuch: number) => boolean;
  /** Basis-Backoff in ms. Standard 300. */
  basisMs?: number;
  /** Deckel für Backoff in ms. Standard 8000. */
  maxMs?: number;
  /** Injizierbare Wartefunktion (für Tests). Standard: echtes setTimeout. */
  sleep?: (ms: number) => Promise<void>;
  /** Optionaler Validator: gilt ein Ergebnis als Erfolg? Sonst wie ein Fehler. */
  gueltig?: (ergebnis: T) => boolean;
}

/**
 * Führt `fn` aus und wiederholt bei Fehlern (oder ungültigem Ergebnis) mit
 * exponentiellem Backoff. Gibt das erste gültige Ergebnis zurück oder wirft den
 * letzten Fehler. Der Sleep ist injizierbar → deterministisch testbar.
 */
export async function mitWiederholung<T>(
  fn: (versuch: number) => Promise<T>,
  opts: WiederholungsOptionen<T> = {},
): Promise<T> {
  const versuche = Math.max(1, opts.versuche ?? 3);
  const sollWiederholen = opts.sollWiederholen ?? (() => true);
  const sleep = opts.sleep ?? ((ms: number) => new Promise((r) => setTimeout(r, ms)));
  const delays = backoffPlan(versuche - 1, opts.basisMs ?? 300, 2, opts.maxMs ?? 8000);

  let letzterFehler: unknown;
  for (let i = 0; i < versuche; i++) {
    try {
      const ergebnis = await fn(i + 1);
      if (opts.gueltig && !opts.gueltig(ergebnis)) {
        letzterFehler = new Error("Ergebnis ungültig");
        if (i < versuche - 1 && sollWiederholen(letzterFehler, i + 1)) {
          await sleep(delays[i]);
          continue;
        }
        throw letzterFehler;
      }
      return ergebnis;
    } catch (fehler) {
      letzterFehler = fehler;
      if (i < versuche - 1 && sollWiederholen(fehler, i + 1)) {
        await sleep(delays[i]);
        continue;
      }
      throw fehler;
    }
  }
  throw letzterFehler;
}
