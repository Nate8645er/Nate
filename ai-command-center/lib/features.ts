/**
 * Feature-Freischaltung je Abo-Stufe – EINE zentrale Quelle der Wahrheit.
 *
 * Grundsatz: Je höher (teurer) das Abo, desto mehr Bereiche des KI-Systems
 * sind nutzbar. Das Gratis-Abo hat bewusst nur die Basis. Diese Matrix ist
 * mit der Vergleichstabelle in `lib/preise.ts` (VERGLEICH) abgestimmt, damit
 * Verkaufsversprechen und tatsächliche Nutzung übereinstimmen.
 *
 * Die Sperre wirkt clientseitig (Plan liegt in localStorage `acc-plan`) über
 * die Komponente `PlanGuard` und die Navigation. Rein informative Seiten
 * (Sicherheit, Status, Einrichtung, Konto, Einstellungen) bleiben immer offen.
 */

import type { PlanId } from "./agents/types";
import type { BereichId } from "@/app/components/WorkNav";

/** Rangfolge der Pläne (klein = günstig). Für Vergleiche „ab Stufe X". */
export const PLAN_RANG: Record<PlanId, number> = {
  FREE: 0,
  PERSONAL: 1,
  STARTER: 2,
  PROFESSIONAL: 3,
  BUSINESS: 4,
  ENTERPRISE: 5,
};

export const PLAN_LABEL: Record<PlanId, string> = {
  FREE: "Gratis",
  PERSONAL: "Solo",
  STARTER: "Start",
  PROFESSIONAL: "Pro",
  BUSINESS: "Business",
  ENTERPRISE: "Enterprise",
};

/** Reihenfolge von günstig nach teuer (für „nächste Stufe"). */
export const PLAN_REIHE: readonly PlanId[] = [
  "FREE",
  "PERSONAL",
  "STARTER",
  "PROFESSIONAL",
  "BUSINESS",
  "ENTERPRISE",
];

/**
 * Mindest-Plan je Bereich. Wer eine tiefere Stufe hat, sieht statt der Seite
 * einen Upgrade-Hinweis. Bereiche ohne Eintrag sind für ALLE offen (Basis).
 *
 * Basis (alle, inkl. FREE): missionen, assistent, skills, freigabe,
 * werkzeuge, onboarding, einstellungen, konto (implizit), status, sicherheit.
 */
export const BEREICH_MIN_PLAN: Partial<Record<BereichId, PlanId>> = {
  // Solo (PERSONAL): erste echte Alltags-Werkzeuge
  email: "PERSONAL",
  berichte: "PERSONAL",
  // Start (STARTER): kleine Teams, Automation & Kernsysteme
  kunden: "STARTER",
  kommando: "STARTER",
  autopilot: "STARTER",
  team: "STARTER",
  agenten: "STARTER",
  integrationen: "STARTER",
  // Pro (PROFESSIONAL): Fachteams, Analyse, Erweiterungen, Team-Zugänge
  analysen: "PROFESSIONAL",
  studio: "PROFESSIONAL",
  erweiterungen: "PROFESSIONAL",
  benutzer: "PROFESSIONAL",
};

/** Route → Bereich (für Seiten-Guards, die nur den Pfad kennen). */
export const ROUTE_BEREICH: Record<string, BereichId> = {
  "/dashboard": "missionen",
  "/assistent": "assistent",
  "/chat": "kommando",
  "/kunden": "kunden",
  "/email": "email",
  "/faehigkeiten": "skills",
  "/workflows": "autopilot",
  "/freigabe": "freigabe",
  "/onboarding": "onboarding",
  "/studio": "studio",
  "/werkzeuge": "werkzeuge",
  "/berichte": "berichte",
  "/analysen": "analysen",
  "/agenten": "agenten",
  "/team": "team",
  "/benutzer": "benutzer",
  "/einstellungen": "einstellungen",
  "/integrationen": "integrationen",
  "/erweiterungen": "erweiterungen",
  "/status": "status",
  "/sicherheit": "sicherheit",
};

/** Hat ein Plan Zugriff auf einen Bereich? */
export function hatZugriff(plan: PlanId, bereich: BereichId): boolean {
  const min = BEREICH_MIN_PLAN[bereich];
  if (!min) return true; // Basis-Bereich, immer offen
  return PLAN_RANG[plan] >= PLAN_RANG[min];
}

/** Der Mindest-Plan für einen Bereich (oder null, wenn Basis/immer offen). */
export function minPlanFuer(bereich: BereichId): PlanId | null {
  return BEREICH_MIN_PLAN[bereich] ?? null;
}

/** Nächsthöherer Plan (für „Upgrade auf …"). Null bei Enterprise. */
export function naechsterPlan(plan: PlanId): PlanId | null {
  const i = PLAN_REIHE.indexOf(plan);
  return i >= 0 && i < PLAN_REIHE.length - 1 ? PLAN_REIHE[i + 1] : null;
}
