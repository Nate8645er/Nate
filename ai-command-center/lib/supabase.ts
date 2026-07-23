/**
 * Supabase-Login – dependency-frei über die GoTrue-Auth-REST-API.
 *
 * Aktivierung: NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY setzen.
 * Ohne diese Werte meldet der Login ehrlich „nicht-konfiguriert" – kein
 * Schein-Login, keine Platzhalter. Die Anon-Keys sind bewusst öffentlich
 * (NEXT_PUBLIC_*); der Schutz kommt aus Supabase Row-Level-Security.
 */

export type SupabaseEnv = Record<string, string | undefined>;

export function supabaseKonfiguriert(env: SupabaseEnv = process.env): boolean {
  const url = env.NEXT_PUBLIC_SUPABASE_URL;
  const key = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  return typeof url === "string" && /^https:\/\/.+\.supabase\.co\/?$/.test(url) &&
    typeof key === "string" && key.length > 20;
}

export interface AuthErgebnis {
  access_token: string;
  refresh_token: string;
  user: { id: string; email: string | null };
}

type AuthAntwort =
  | { ok: true; sitzung: AuthErgebnis }
  | { ok: false; error: "nicht-konfiguriert" | "ungueltige-daten" | "auth-fehler"; meldung?: string };

function basis(env: SupabaseEnv): string {
  return (env.NEXT_PUBLIC_SUPABASE_URL ?? "").replace(/\/$/, "");
}

async function authAnfrage(
  pfad: string,
  body: Record<string, string>,
  env: SupabaseEnv,
  fetchImpl: typeof fetch,
): Promise<AuthAntwort> {
  if (!supabaseKonfiguriert(env)) return { ok: false, error: "nicht-konfiguriert" };
  const key = env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;
  try {
    const res = await fetchImpl(`${basis(env)}${pfad}`, {
      method: "POST",
      headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json()) as Record<string, unknown>;
    if (!res.ok) {
      const meldung = typeof data.msg === "string" ? data.msg
        : typeof data.error_description === "string" ? data.error_description : undefined;
      return { ok: false, error: "auth-fehler", meldung };
    }
    const user = data.user as { id?: string; email?: string } | undefined;
    if (typeof data.access_token !== "string" || !user?.id) {
      return { ok: false, error: "auth-fehler" };
    }
    return {
      ok: true,
      sitzung: {
        access_token: data.access_token,
        refresh_token: typeof data.refresh_token === "string" ? data.refresh_token : "",
        user: { id: user.id, email: user.email ?? null },
      },
    };
  } catch {
    return { ok: false, error: "auth-fehler" };
  }
}

/** Anmeldung mit E-Mail + Passwort. */
export async function anmelden(
  email: string,
  passwort: string,
  env: SupabaseEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<AuthAntwort> {
  if (!email || !passwort) return { ok: false, error: "ungueltige-daten" };
  return authAnfrage("/auth/v1/token?grant_type=password", { email, password: passwort }, env, fetchImpl);
}

/** Registrierung mit E-Mail + Passwort. */
export async function registrieren(
  email: string,
  passwort: string,
  env: SupabaseEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<AuthAntwort> {
  if (!email || !passwort) return { ok: false, error: "ungueltige-daten" };
  return authAnfrage("/auth/v1/signup", { email, password: passwort }, env, fetchImpl);
}
