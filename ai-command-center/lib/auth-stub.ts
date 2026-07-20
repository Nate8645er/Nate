/**
 * Auth-Stub – Platzhalter-Interfaces fuer Phase 2 (NextAuth + Postgres).
 *
 * Diese Datei definiert die Datenmodelle, gegen die die App bereits jetzt
 * typisiert werden kann. In Phase 2 wird die Implementierung durch
 * NextAuth (Session-Handling) und Postgres (Persistenz) ersetzt,
 * ohne dass sich die Aufrufer-Schnittstelle aendert.
 *
 * TODO Phase 2:
 *  - NextAuth mit E-Mail-Magic-Link + Google-OAuth konfigurieren
 *  - User/Team in Postgres persistieren (z. B. Drizzle ORM)
 *  - getCurrentUser() aus der Server-Session lesen
 *  - Middleware: /dashboard und /api/mission nur fuer eingeloggte Nutzer
 */

export interface User {
  id: string;
  email: string;
  name: string;
  /** Team, dem der Nutzer angehoert (1 Team pro Nutzer im MVP-Modell). */
  teamId: string;
  createdAt: string; // ISO-8601
}

export interface Team {
  id: string;
  name: string;
  /** Referenz auf die aktive Subscription (lib/billing-stub.ts). */
  subscriptionId: string | null;
  createdAt: string; // ISO-8601
}

/**
 * Liefert den aktuellen Nutzer der Session.
 *
 * MVP: immer ein Demo-Nutzer, damit Dashboard und API ohne Login laufen.
 * Phase 2: echte Session-Aufloesung via NextAuth; `null` bei fehlender Session.
 */
export async function getCurrentUser(): Promise<User | null> {
  return {
    id: "demo-user",
    email: "demo@example.com",
    name: "Demo Nutzer",
    teamId: "demo-team",
    createdAt: new Date(0).toISOString(),
  };
}
