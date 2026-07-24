/**
 * Server-seitige Anbindung an das platform-backend (Enterprise-Schicht).
 *
 * Additiv und ehrlich: Ist `PLATFORM_BACKEND_URL` nicht gesetzt oder das
 * Backend nicht erreichbar, liefert `fetchCompute()` `null` — das v2-Dashboard
 * zeigt dann unverändert „—" („Backend nicht verbunden") statt erfundener
 * Werte. Kein Import aus dem Python-Repo; reiner fetch mit kurzem Timeout,
 * damit ein nicht laufendes Backend die Seite nie blockiert.
 */

export interface ComputeDevice {
  id: string;
  vendor: "nvidia" | "amd" | "apple" | "cpu";
  name: string;
  arch: string | null;
  memory_total_mb: number;
  memory_model: "dedicated" | "unified";
  backends: string[];
  capabilities: string[];
}

export interface ComputeResponse {
  gpu_available: boolean;
  device_count: number;
  devices: ComputeDevice[];
}

/** Basis-URL des Backends aus der Umgebung (leer = nicht konfiguriert). */
export function backendBaseUrl(env: Record<string, string | undefined> = process.env): string | null {
  const url = (env.PLATFORM_BACKEND_URL ?? "").trim().replace(/\/$/, "");
  return url || null;
}

/**
 * Holt die echten Compute-Daten vom Backend. Gibt `null` zurück, wenn nicht
 * konfiguriert, nicht erreichbar, Timeout oder unerwartete Antwort — nie werfen.
 */
export async function fetchCompute(
  opts: { baseUrl?: string | null; timeoutMs?: number; fetchImpl?: typeof fetch } = {},
): Promise<ComputeResponse | null> {
  const base = opts.baseUrl !== undefined ? opts.baseUrl : backendBaseUrl();
  if (!base) return null;
  const f = opts.fetchImpl ?? fetch;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 1200);
  try {
    const res = await f(base + "/health/compute", {
      headers: { accept: "application/json" },
      signal: ctrl.signal,
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as ComputeResponse;
    if (!data || !Array.isArray(data.devices)) return null;
    return data;
  } catch {
    return null; // honest: Backend down/timeout → „—"
  } finally {
    clearTimeout(timer);
  }
}

/** Formatiert MB als „GB" für die Kacheln (z. B. 16075 → „15.7 GB"). */
export function formatMemoryGb(mb: number): string {
  if (!Number.isFinite(mb) || mb <= 0) return "—";
  return (mb / 1024).toFixed(1) + " GB";
}

/** Wählt das primäre Rechen-Gerät (GPU bevorzugt, sonst CPU). */
export function primaryDevice(c: ComputeResponse | null): ComputeDevice | null {
  if (!c || c.devices.length === 0) return null;
  return c.devices.find((d) => d.vendor !== "cpu") ?? c.devices[0];
}

// --------------------------------------------------------------------------- //
// Modell-Routing (HTTP-API v1) — reine Policy, kein Secret, kein Token nötig.
// --------------------------------------------------------------------------- //
export type DataClass = "local_only" | "internal" | "public";

export interface RouteRequest {
  prompt_tokens_est?: number;
  data_class?: DataClass;
  needs?: string[];
  local_available?: boolean;
  local_capabilities?: string[];
  cloud_available?: boolean;
  local_load_pct?: number;
}

export interface RouteResponse {
  placement: "local" | "cloud";
  reason: string;
  fallback: "local" | "cloud" | null;
}

/** Menschlich lesbares Label für die Routing-Entscheidung (v2-UI). */
export function describePlacement(d: RouteResponse | null): { label: string; hint: string } {
  if (!d) return { label: "—", hint: "Backend nicht verbunden" };
  const wo = d.placement === "local" ? "Lokal (im Haus)" : "Cloud";
  return { label: wo, hint: d.reason };
}

/**
 * Fragt die Routing-Entscheidung des Backends ab (local ↔ cloud + Begründung).
 * Gibt `null` zurück, wenn nicht konfiguriert/nicht erreichbar/Timeout — nie werfen.
 */
export async function routeModel(
  body: RouteRequest,
  opts: { baseUrl?: string | null; timeoutMs?: number; fetchImpl?: typeof fetch } = {},
): Promise<RouteResponse | null> {
  const base = opts.baseUrl !== undefined ? opts.baseUrl : backendBaseUrl();
  if (!base) return null;
  const f = opts.fetchImpl ?? fetch;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 1200);
  try {
    const res = await f(base + "/api/v1/models/route", {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as RouteResponse;
    if (!data || (data.placement !== "local" && data.placement !== "cloud")) return null;
    return data;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

// --------------------------------------------------------------------------- //
// Mission-Delegation (Cutover) — Auftrag ans Backend geben (RBAC agent:run).
// --------------------------------------------------------------------------- //
export interface MissionResult {
  ok: boolean;
  placement: string | null;
  reason: string | null;
  text: string | null;
  error: string | null;
}

/**
 * Delegiert eine Mission an POST /api/v1/missions des Backends. Erfordert ein
 * Bearer-Token (Keycloak). Gibt `null` zurück, wenn nicht konfiguriert, kein
 * Token, nicht erreichbar oder Backend meldet „nicht ausführbar" — der Aufrufer
 * fällt dann ehrlich auf den bestehenden lokalen Orchestrator zurück.
 */
export async function runMissionViaBackend(
  goal: string,
  token: string | null | undefined,
  opts: { baseUrl?: string | null; timeoutMs?: number; fetchImpl?: typeof fetch } = {},
): Promise<MissionResult | null> {
  const base = opts.baseUrl !== undefined ? opts.baseUrl : backendBaseUrl();
  if (!base || !token) return null; // ohne Backend-URL oder Token: kein Delegieren
  const f = opts.fetchImpl ?? fetch;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 30000);
  try {
    const res = await f(base + "/api/v1/missions", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "application/json",
        authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ goal }),
      signal: ctrl.signal,
      cache: "no-store",
    });
    if (!res.ok) return null; // 401/403/503 → Fallback auf lokalen Orchestrator
    const data = (await res.json()) as MissionResult;
    return data?.ok ? data : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}
