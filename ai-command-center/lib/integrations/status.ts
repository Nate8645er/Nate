/**
 * Status-/Health-Logik der Integrationen. Rein lesend, wirft nie – der Aufrufer
 * bekommt immer einen definierten Status zurück (ehrlich „nicht-konfiguriert",
 * wenn die nötigen Umgebungsvariablen fehlen).
 */

import type { Integration, IntegrationStatus } from "./types";

type Env = Record<string, string | undefined>;

/** Ist die Integration über Umgebungsvariablen aktiviert? */
export function istKonfiguriert(i: Integration, env: Env = process.env): boolean {
  if (i.immerAktiv) return true;
  if (i.envKeys.length === 0) return false;
  return i.envKeys.every((k) => {
    const v = env[k];
    return typeof v === "string" && v.trim().length > 0;
  });
}

/** Grundstatus ohne Netzwerk (schnell, synchron). */
export function grundStatus(i: Integration, env: Env = process.env): IntegrationStatus {
  if (i.immerAktiv) return "bereit";
  return istKonfiguriert(i, env) ? "konfiguriert" : "nicht-konfiguriert";
}

/** Basis-URL für den Health-Check (ohne abschliessenden Slash). */
export function healthUrl(i: Integration, env: Env = process.env): string | null {
  if (!i.healthUrlEnv || !i.healthPfad) return null;
  const base = env[i.healthUrlEnv];
  if (!base) return null;
  return base.replace(/\/+$/, "") + i.healthPfad;
}

/**
 * Optionaler Health-Check per HTTP (serverseitig). Prüft nur erreichbare,
 * konfigurierte Dienste; nutzt ein kurzes Timeout und schluckt alle Fehler.
 */
export async function pingIntegration(
  i: Integration,
  opts: { env?: Env; timeoutMs?: number; fetchImpl?: typeof fetch } = {},
): Promise<IntegrationStatus> {
  const env = opts.env ?? process.env;
  const grund = grundStatus(i, env);
  if (grund !== "konfiguriert") return grund;

  const url = healthUrl(i, env);
  if (!url) return "konfiguriert";

  const f = opts.fetchImpl ?? fetch;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 4000);
  try {
    const res = await f(url, { signal: ctrl.signal, method: "GET" });
    return res.ok ? "aktiv" : "konfiguriert";
  } catch {
    // Nicht erreichbar → bleibt „konfiguriert" (ENV gesetzt, Dienst offline).
    return "konfiguriert";
  } finally {
    clearTimeout(timer);
  }
}
