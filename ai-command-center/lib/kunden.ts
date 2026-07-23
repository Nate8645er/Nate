/**
 * Kunden-/Abo-Speicher – dependency-frei über Supabase PostgREST.
 *
 * Zweck: Nach einem verifizierten Stripe-Webhook wird hier das Abo eines Kunden
 * gespeichert (Plan-Freischaltung), und das Kundenportal schlägt die Stripe-
 * `customerId` sicher aus der angemeldeten Sitzung (E-Mail) nach.
 *
 * Aktivierung: NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY setzen.
 * Der Service-Role-Key ist ein SERVERSEITIGES GEHEIMNIS (umgeht RLS) – niemals
 * an den Client geben, niemals NEXT_PUBLIC_. Ohne Key: ehrlich „nicht-konfiguriert".
 *
 * Tabelle `abos` (siehe supabase/schema.sql):
 *   customer_id text primary key, email text, plan_id text, status text,
 *   aktualisiert_am timestamptz.
 */

export type KundenEnv = Record<string, string | undefined>;

export interface Abo {
  customer_id: string;
  email: string | null;
  plan_id: string;
  status: string;
}

export function kundenStoreKonfiguriert(env: KundenEnv = process.env): boolean {
  const url = env.NEXT_PUBLIC_SUPABASE_URL;
  const key = env.SUPABASE_SERVICE_ROLE_KEY;
  return typeof url === "string" && /^https:\/\/.+\.supabase\.co\/?$/.test(url) &&
    typeof key === "string" && key.length > 20;
}

function rest(env: KundenEnv): { basis: string; key: string } {
  return {
    basis: (env.NEXT_PUBLIC_SUPABASE_URL ?? "").replace(/\/$/, "") + "/rest/v1",
    key: env.SUPABASE_SERVICE_ROLE_KEY as string,
  };
}

/**
 * Schaltet ein Abo frei bzw. aktualisiert es (Upsert auf customer_id).
 * Wird aus dem verifizierten Webhook aufgerufen.
 */
export async function aboFreischalten(
  abo: Abo,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<{ ok: true } | { ok: false; error: "nicht-konfiguriert" | "ungueltige-daten" | "db-fehler" }> {
  if (!kundenStoreKonfiguriert(env)) return { ok: false, error: "nicht-konfiguriert" };
  if (!abo.customer_id || !abo.plan_id) return { ok: false, error: "ungueltige-daten" };
  const { basis, key } = rest(env);
  try {
    const res = await fetchImpl(`${basis}/abos?on_conflict=customer_id`, {
      method: "POST",
      headers: {
        apikey: key,
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        // Upsert: bei Konflikt aktualisieren statt Fehler.
        Prefer: "resolution=merge-duplicates,return=minimal",
      },
      body: JSON.stringify({
        customer_id: abo.customer_id,
        email: abo.email,
        plan_id: abo.plan_id,
        status: abo.status,
      }),
    });
    return res.ok ? { ok: true } : { ok: false, error: "db-fehler" };
  } catch {
    return { ok: false, error: "db-fehler" };
  }
}

async function abosLesen(
  filter: string,
  env: KundenEnv,
  fetchImpl: typeof fetch,
): Promise<Abo[] | null> {
  if (!kundenStoreKonfiguriert(env)) return null;
  const { basis, key } = rest(env);
  try {
    const res = await fetchImpl(`${basis}/abos?${filter}`, {
      headers: { apikey: key, Authorization: `Bearer ${key}` },
    });
    if (!res.ok) return null;
    return (await res.json()) as Abo[];
  } catch {
    return null;
  }
}

/** Liest das Abo zu einer Stripe-customerId (oder null). */
export async function aboLesen(
  customerId: string,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<Abo | null> {
  if (!customerId) return null;
  const rows = await abosLesen(`customer_id=eq.${encodeURIComponent(customerId)}&limit=1`, env, fetchImpl);
  return rows && rows.length > 0 ? rows[0] : null;
}

/** Schlägt die Stripe-customerId zu einer E-Mail nach (für das Kundenportal). */
export async function customerIdFuerEmail(
  email: string,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<string | null> {
  if (!email) return null;
  const rows = await abosLesen(
    `email=eq.${encodeURIComponent(email)}&order=aktualisiert_am.desc&limit=1`,
    env,
    fetchImpl,
  );
  return rows && rows.length > 0 ? rows[0].customer_id : null;
}
