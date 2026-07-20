/**
 * Billing-Stub – Platzhalter-Interfaces fuer Phase 3 (Stripe).
 *
 * Die Plan-Definitionen werden bereits jetzt von der Landing Page
 * (Preistabelle) genutzt; die Subscription-Logik folgt in Phase 3.
 *
 * TODO Phase 3:
 *  - Stripe Checkout + Customer Portal integrieren
 *  - Webhooks (invoice.paid, customer.subscription.updated) verarbeiten
 *  - Missions-Kontingent je Plan in /api/mission durchsetzen
 *  - Usage-Tracking (LLM-Kosten pro Mission) je Team aufzeichnen
 */

export type PlanId = "free" | "starter" | "professional" | "business" | "enterprise";

export interface Plan {
  id: PlanId;
  name: string;
  /** Monatspreis in EUR; null = individuell (Enterprise). */
  pricePerMonth: number | null;
  /** Missionen pro Monat; null = unbegrenzt. */
  missionsPerMonth: number | null;
  features: string[];
  highlighted: boolean;
}

export interface Subscription {
  id: string;
  teamId: string;
  planId: PlanId;
  status: "active" | "trialing" | "past_due" | "canceled";
  /** Stripe-Subscription-ID (Phase 3). */
  stripeSubscriptionId: string | null;
  currentPeriodEnd: string; // ISO-8601
}

/** Preisstufen – Quelle fuer die Landing-Page-Preistabelle. */
export const PLANS: Plan[] = [
  {
    id: "free",
    name: "Free",
    pricePerMonth: 0,
    missionsPerMonth: 5,
    features: [
      "5 Missionen pro Monat",
      "Alle 4 Agenten",
      "Mission Control Dashboard",
      "Community Support",
    ],
    highlighted: false,
  },
  {
    id: "starter",
    name: "Starter",
    pricePerMonth: 299,
    missionsPerMonth: 100,
    features: [
      "100 Missionen pro Monat",
      "Alle 4 Agenten",
      "Missions-Verlauf",
      "E-Mail Support",
      "1 Teammitglied",
    ],
    highlighted: false,
  },
  {
    id: "professional",
    name: "Professional",
    pricePerMonth: 999,
    missionsPerMonth: 500,
    features: [
      "500 Missionen pro Monat",
      "Alle 4 Agenten",
      "Prioritaets-Verarbeitung",
      "Bis zu 5 Teammitglieder",
      "Prioritaets-Support",
    ],
    highlighted: true,
  },
  {
    id: "business",
    name: "Business",
    pricePerMonth: 2999,
    missionsPerMonth: 2000,
    features: [
      "2000 Missionen pro Monat",
      "Alle 4 Agenten",
      "Bis zu 20 Teammitglieder",
      "API-Zugang",
      "Dedizierter Ansprechpartner",
    ],
    highlighted: false,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    pricePerMonth: null,
    missionsPerMonth: null,
    features: [
      "Unbegrenzte Missionen",
      "Eigene Agenten-Konfiguration",
      "White-Label Option",
      "SSO und Audit-Logs",
      "SLA und Onboarding",
    ],
    highlighted: false,
  },
];

/**
 * Liefert die Subscription eines Teams.
 * MVP: immer Free-Plan. Phase 3: Lookup in Postgres/Stripe.
 */
export async function getSubscription(teamId: string): Promise<Subscription> {
  return {
    id: `sub-${teamId}`,
    teamId,
    planId: "free",
    status: "active",
    stripeSubscriptionId: null,
    currentPeriodEnd: new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString(),
  };
}
