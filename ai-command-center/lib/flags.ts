/**
 * Feature-Flags – ehrliche Defaults, additiv.
 *
 * Das neue Premium-UI (v2, Phase 7) liegt hinter `ui_v2`. Solange das Flag aus
 * ist, ändert sich am bestehenden Produkt nichts; das alte UI bleibt lauffähig,
 * bis das neue die Kernwege abdeckt (Vorgabe §7). Umschalten über die Umgebung
 * (`NEXT_PUBLIC_UI_V2=1`) oder – clientseitig – über localStorage `acc-ui-v2`.
 */

export type FlagName = "ui_v2" | "platform_backend" | "keycloak_auth";

/** Serverseitig (Env). */
export function flagFromEnv(name: FlagName, env: Record<string, string | undefined> = process.env): boolean {
  const map: Record<FlagName, string> = {
    ui_v2: "NEXT_PUBLIC_UI_V2",
    // Cutover: Missionen an das neue platform-backend delegieren (statt lokalem
    // Orchestrator). Standardmäßig AUS → bestehendes Verhalten unverändert.
    platform_backend: "NEXT_PUBLIC_USE_PLATFORM_BACKEND",
    // Cutover: Keycloak/OIDC-Login als Alternative zu Supabase. Standard AUS.
    keycloak_auth: "NEXT_PUBLIC_KEYCLOAK_AUTH",
  };
  return truthy(env[map[name]]);
}

/** Aus einem beliebigen Roh-Wert (localStorage/Query). */
export function flagFromValue(value: string | null | undefined): boolean {
  return truthy(value);
}

function truthy(v: string | null | undefined): boolean {
  if (!v) return false;
  const s = v.trim().toLowerCase();
  return s === "1" || s === "true" || s === "on" || s === "yes";
}
