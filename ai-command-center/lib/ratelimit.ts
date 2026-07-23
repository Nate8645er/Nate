/**
 * Rate-Limiting – dependency-frei. Bevorzugt einen geteilten Zähler über Upstash
 * Redis (REST), der über alle Serverless-Instanzen hinweg zählt. Ohne Upstash
 * greift ein Best-Effort-In-Memory-Zähler (nur pro Instanz) – ehrlich schwächer,
 * aber besser als nichts. Fixed-Window-Zähler.
 *
 * Aktivierung (empfohlen für Produktion): UPSTASH_REDIS_REST_URL +
 * UPSTASH_REDIS_REST_TOKEN setzen.
 */

export type RateLimitEnv = Record<string, string | undefined>;

export function rateLimitVerteilt(env: RateLimitEnv = process.env): boolean {
  return Boolean(env.UPSTASH_REDIS_REST_URL && env.UPSTASH_REDIS_REST_TOKEN);
}

export interface RateLimitErgebnis {
  erlaubt: boolean;
  verbleibend: number;
  resetSek: number;
  modus: "upstash" | "speicher";
}

// Instanz-lokaler Fallback-Speicher (nur wirksam, solange die Instanz lebt).
const speicher = new Map<string, { count: number; resetMs: number }>();

function speicherPruefen(
  schluessel: string,
  limit: number,
  fensterSek: number,
  jetztMs: number,
): RateLimitErgebnis {
  const eintrag = speicher.get(schluessel);
  if (!eintrag || eintrag.resetMs <= jetztMs) {
    speicher.set(schluessel, { count: 1, resetMs: jetztMs + fensterSek * 1000 });
    return { erlaubt: true, verbleibend: limit - 1, resetSek: fensterSek, modus: "speicher" };
  }
  eintrag.count += 1;
  const resetSek = Math.max(0, Math.ceil((eintrag.resetMs - jetztMs) / 1000));
  return {
    erlaubt: eintrag.count <= limit,
    verbleibend: Math.max(0, limit - eintrag.count),
    resetSek,
    modus: "speicher",
  };
}

/**
 * Prüft und erhöht den Zähler für `schluessel`. Gibt zurück, ob die Anfrage
 * erlaubt ist. Bei Upstash-Fehlern wird bewusst auf „erlaubt" ausgewichen
 * (fail-open), damit ein Störfall im Limiter den Login nicht komplett blockiert.
 */
export async function pruefeRateLimit(
  schluessel: string,
  limit: number,
  fensterSek: number,
  env: RateLimitEnv = process.env,
  fetchImpl: typeof fetch = fetch,
  jetztMs: number = Date.now(),
): Promise<RateLimitErgebnis> {
  if (!rateLimitVerteilt(env)) {
    return speicherPruefen(schluessel, limit, fensterSek, jetztMs);
  }
  const url = (env.UPSTASH_REDIS_REST_URL as string).replace(/\/$/, "");
  const token = env.UPSTASH_REDIS_REST_TOKEN as string;
  try {
    // Pipeline: INCR und (nur beim ersten Treffer) EXPIRE für ein festes Fenster.
    const res = await fetchImpl(`${url}/pipeline`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify([
        ["INCR", schluessel],
        ["EXPIRE", schluessel, String(fensterSek), "NX"],
      ]),
    });
    if (!res.ok) return { erlaubt: true, verbleibend: limit, resetSek: fensterSek, modus: "upstash" };
    const daten = (await res.json()) as Array<{ result?: number }>;
    const count = typeof daten?.[0]?.result === "number" ? daten[0].result : 1;
    return {
      erlaubt: count <= limit,
      verbleibend: Math.max(0, limit - count),
      resetSek: fensterSek,
      modus: "upstash",
    };
  } catch {
    // Fail-open: Limiter-Störung darf den Dienst nicht lahmlegen.
    return { erlaubt: true, verbleibend: limit, resetSek: fensterSek, modus: "upstash" };
  }
}

/** Client-IP aus den üblichen Proxy-Headern (Vercel/Standard). */
export function clientIp(headers: Headers): string {
  const xff = headers.get("x-forwarded-for");
  if (xff) return xff.split(",")[0].trim();
  return headers.get("x-real-ip") || "unbekannt";
}

/**
 * Limit für Auth-Endpunkte: pro IP+E-Mail. Standard 10 Versuche / 10 Minuten –
 * bremst Brute-Force/Enumeration, ohne echte Nutzer zu behindern.
 */
export async function authLimitPruefen(
  request: Request,
  aktion: string,
  email: string,
  env: RateLimitEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<RateLimitErgebnis> {
  const ip = clientIp(request.headers);
  const key = `rl:${aktion}:${ip}:${email.toLowerCase()}`;
  return pruefeRateLimit(key, 10, 600, env, fetchImpl);
}
