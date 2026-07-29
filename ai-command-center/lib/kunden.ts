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
  /** Event-Zeit (Unix-Sekunden) des zugrunde liegenden Stripe-Ereignisses. */
  event_zeit?: number;
  /** Einmalig erzeugter Lizenzschlüssel (nach dem Kauf). */
  license_key?: string | null;
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
): Promise<{ ok: true } | { ok: false; error: "nicht-konfiguriert" | "ungueltige-daten" | "db-fehler" | "veraltet" }> {
  if (!kundenStoreKonfiguriert(env)) return { ok: false, error: "nicht-konfiguriert" };
  if (!abo.customer_id || !abo.plan_id) return { ok: false, error: "ungueltige-daten" };

  // Reihenfolge-Schutz: Stripe garantiert keine Zustellreihenfolge und stellt bei
  // Fehlern erneut zu. Ein verspätetes "updated" (active) darf ein späteres
  // "deleted" (canceled) nicht überschreiben. Nur anwenden, wenn das Ereignis
  // neuer ist als der gespeicherte Stand.
  if (abo.event_zeit && abo.event_zeit > 0) {
    const vorhanden = await aboLesen(abo.customer_id, env, fetchImpl);
    if (vorhanden && (vorhanden.event_zeit ?? 0) > abo.event_zeit) {
      return { ok: false, error: "veraltet" };
    }
  }

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
        event_zeit: abo.event_zeit ?? 0,
        // license_key wird hier NICHT geschrieben – das Setzen läuft atomar über
        // lizenzSchluesselSetzen (nur wenn noch NULL), um Doppelschlüssel bei
        // parallelen Webhook-Zustellungen zu verhindern.
      }),
    });
    return res.ok ? { ok: true } : { ok: false, error: "db-fehler" };
  } catch {
    return { ok: false, error: "db-fehler" };
  }
}

/**
 * Setzt den Lizenzschlüssel ATOMAR – nur wenn noch keiner gesetzt ist
 * (`license_key IS NULL`). Gibt `{ gesetzt: true }` nur zurück, wenn genau dieser
 * Aufruf den Schlüssel eingetragen hat. So erzeugen parallele Webhook-
 * Zustellungen (Stripe: at-least-once) niemals zwei gültige Schlüssel/Mails:
 * der zweite Aufruf trifft 0 Zeilen (license_key nicht mehr NULL) → gesetzt=false.
 */
export async function lizenzSchluesselSetzen(
  customerId: string,
  key: string,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<{ gesetzt: boolean }> {
  if (!kundenStoreKonfiguriert(env) || !customerId || !key) return { gesetzt: false };
  const { basis, key: srv } = rest(env);
  try {
    const res = await fetchImpl(
      `${basis}/abos?customer_id=eq.${encodeURIComponent(customerId)}&license_key=is.null`,
      {
        method: "PATCH",
        headers: {
          apikey: srv,
          Authorization: `Bearer ${srv}`,
          "Content-Type": "application/json",
          // Repräsentation zurückgeben, um zu erkennen, ob eine Zeile getroffen wurde.
          Prefer: "return=representation",
        },
        body: JSON.stringify({ license_key: key }),
      },
    );
    if (!res.ok) return { gesetzt: false };
    const rows = (await res.json()) as unknown[];
    return { gesetzt: Array.isArray(rows) && rows.length > 0 };
  } catch {
    return { gesetzt: false };
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

/** Liest das (neueste) Abo zu einer E-Mail – für Konto/Dashboard. */
export async function aboFuerEmail(
  email: string,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<Abo | null> {
  if (!email) return null;
  const rows = await abosLesen(
    `email=eq.${encodeURIComponent(email)}&order=aktualisiert_am.desc&limit=1`,
    env,
    fetchImpl,
  );
  return rows && rows.length > 0 ? rows[0] : null;
}

/** Schlägt die Stripe-customerId zu einer E-Mail nach (für das Kundenportal). */
export async function customerIdFuerEmail(
  email: string,
  env: KundenEnv = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<string | null> {
  const abo = await aboFuerEmail(email, env, fetchImpl);
  return abo ? abo.customer_id : null;
}
