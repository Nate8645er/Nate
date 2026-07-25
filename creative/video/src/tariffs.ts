// Tarif-Daten fuer das Video. Eine Wahrheit mit ../tariffs.json (SVG-Pipeline)
// und platform-backend/migrations/002_seed_plans.sql. Aendert sich ein Tarif,
// wird diese Datei manuell synchron gehalten (kein Build-Step importiert JSON
// nach TS in dieser einfachen Pipeline — bewusst, siehe README).
export interface Tariff {
  code: string;
  name: string;
  priceDisplay: string;
  audience: string;
  features: string[];
}

export const BRAND = 'KI-Plattform';
export const VAT_NOTE = 'Preise CHF inkl. MwSt';

export const TARIFFS: Tariff[] = [
  {
    code: 'free',
    name: 'Free',
    priceDisplay: 'Kostenlos',
    audience: 'Zum Testen',
    features: ['1 lokales Modell', '1 Agent', "100'000 Tokens/Monat"],
  },
  {
    code: 'starter',
    name: 'Starter',
    priceDisplay: 'CHF 19.00 / Monat',
    audience: 'Einzelunternehmer',
    features: ['Schnelle Cloud-Modelle', '3 Agenten', '2 Mio. Tokens/Monat'],
  },
  {
    code: 'pro',
    name: 'Pro',
    priceDisplay: 'CHF 49.00 / Monat',
    audience: 'KMU',
    features: ['Cloud- + lokale Modelle', '10 Agenten', '10 Mio. Tokens/Monat'],
  },
  {
    code: 'business',
    name: 'Business',
    priceDisplay: 'CHF 149.00 / Monat',
    audience: 'Teams',
    features: ['Alle Modelle, freie Wahl', '30 Agenten', 'SSO + Team-Verwaltung'],
  },
  {
    code: 'enterprise',
    name: 'Enterprise',
    priceDisplay: 'Auf Anfrage',
    audience: 'Konzern / Individuell',
    features: ['Dedizierte Instanz', 'Unbegrenzte Agenten', 'SLA + Onboarding'],
  },
];
