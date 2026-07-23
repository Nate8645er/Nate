/**
 * ROI-Schätzung: rechnet aus Branche, Teamgröße und Abo-Stufe eine ehrliche
 * Schätzung der monatlichen Zeit- und Kostenersparnis. Reiner, testbarer Kern
 * (keine Abhängigkeiten, keine Zufalls-/Zeitquellen) – die UI zeigt die Werte
 * als klar gekennzeichnete Schätzung, nicht als Versprechen.
 *
 * Annahmen sind bewusst konservativ und offengelegt (siehe `annahmen`), damit
 * nichts vorgetäuscht wird.
 */

export type BranchenId =
  | "handel"
  | "handwerk"
  | "gastro"
  | "dienstleistung"
  | "gesundheit"
  | "marketing"
  | "andere";

export interface Branche {
  id: BranchenId;
  name: string;
  /** Realistischer, konservativer Stundensatz (CHF) für den Ersparniswert. */
  stundensatz: number;
  /** Wiederkehrende, automatisierbare Aufgaben pro Woche (Basiswert Solo). */
  aufgabenProWoche: number;
  /** Durchschnittliche Minuten je Aufgabe (manuell). */
  minutenProAufgabe: number;
}

/** Branchen-Defaults – konservativ gewählt (lieber untertreiben). */
export const BRANCHEN: readonly Branche[] = [
  { id: "handel", name: "Handel / E-Commerce", stundensatz: 55, aufgabenProWoche: 18, minutenProAufgabe: 18 },
  { id: "handwerk", name: "Handwerk / Bau", stundensatz: 70, aufgabenProWoche: 12, minutenProAufgabe: 20 },
  { id: "gastro", name: "Gastronomie", stundensatz: 45, aufgabenProWoche: 14, minutenProAufgabe: 15 },
  { id: "dienstleistung", name: "Dienstleistung / Beratung", stundensatz: 90, aufgabenProWoche: 16, minutenProAufgabe: 22 },
  { id: "gesundheit", name: "Gesundheit / Praxis", stundensatz: 75, aufgabenProWoche: 12, minutenProAufgabe: 18 },
  { id: "marketing", name: "Marketing / Agentur", stundensatz: 85, aufgabenProWoche: 22, minutenProAufgabe: 20 },
  { id: "andere", name: "Andere", stundensatz: 65, aufgabenProWoche: 15, minutenProAufgabe: 18 },
];

/** Teamgrößen-Stufen mit einem Multiplikator auf das Aufgabenvolumen. */
export interface Teamgroesse {
  id: string;
  name: string;
  faktor: number;
}
export const TEAMGROESSEN: readonly Teamgroesse[] = [
  { id: "solo", name: "Solo (1)", faktor: 1 },
  { id: "klein", name: "2–10", faktor: 3.2 },
  { id: "mittel", name: "11–50", faktor: 9 },
  { id: "gross", name: "50+", faktor: 20 },
];

/**
 * Anteil der Aufgaben, den das jeweilige Abo realistisch automatisiert
 * übernehmen kann (0–1). Höhere Stufen = mehr parallele Spezialisten.
 */
export const ABDECKUNG_PRO_PLAN: Record<string, number> = {
  FREE: 0.08,
  PERSONAL: 0.2,
  STARTER: 0.32,
  PROFESSIONAL: 0.5,
  BUSINESS: 0.68,
  ENTERPRISE: 0.8,
};

export interface RoiEingabe {
  branche: BranchenId;
  teamgroesse: string;
  plan?: string;
}

export interface RoiErgebnis {
  /** Automatisierte Aufgaben pro Monat (gerundet). */
  aufgabenProMonat: number;
  /** Eingesparte Arbeitsstunden pro Monat (gerundet). */
  stundenProMonat: number;
  /** Geschätzte Kostenersparnis pro Monat in CHF (gerundet auf 10). */
  chfProMonat: number;
  /** Offengelegte Annahmen (für die UI, damit nichts vorgetäuscht wird). */
  annahmen: string;
}

const clampFaktor = 4.345; // Wochen pro Monat (52/12)

function findeBranche(id: BranchenId): Branche {
  return BRANCHEN.find((b) => b.id === id) ?? BRANCHEN[BRANCHEN.length - 1];
}
function findeTeam(id: string): Teamgroesse {
  return TEAMGROESSEN.find((t) => t.id === id) ?? TEAMGROESSEN[0];
}

/**
 * Berechnet die ROI-Schätzung. Deterministisch, wirft nie – unbekannte IDs
 * fallen auf sichere Defaults zurück. Werte sind konservative Schätzungen.
 */
export function roiSchaetzung(eingabe: RoiEingabe): RoiErgebnis {
  const b = findeBranche(eingabe.branche);
  const t = findeTeam(eingabe.teamgroesse);
  const plan = eingabe.plan && eingabe.plan in ABDECKUNG_PRO_PLAN ? eingabe.plan : "PROFESSIONAL";
  const abdeckung = ABDECKUNG_PRO_PLAN[plan];

  const aufgabenWoche = b.aufgabenProWoche * t.faktor * abdeckung;
  const aufgabenMonat = aufgabenWoche * clampFaktor;
  const stundenMonat = (aufgabenMonat * b.minutenProAufgabe) / 60;
  const chfMonat = stundenMonat * b.stundensatz;

  return {
    aufgabenProMonat: Math.round(aufgabenMonat),
    stundenProMonat: Math.round(stundenMonat),
    chfProMonat: Math.round(chfMonat / 10) * 10,
    annahmen: `Schätzung: ${b.name}, ${t.name}, Plan ${plan}. Grundlage: ~${b.aufgabenProWoche} automatisierbare Aufgaben/Woche pro Person, ${b.minutenProAufgabe} Min/Aufgabe, ${Math.round(abdeckung * 100)}% Abdeckung durch das Abo, Stundensatz CHF ${b.stundensatz}. Konservativ – echte Werte hängen von Ihrer Nutzung ab.`,
  };
}
