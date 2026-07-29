/**
 * Shopify -> Lizenz-Auslieferung (pure Logik, ohne Netz/HTTP).
 *
 * Ordnet die gekauften Bestell-Positionen den Abo-Stufen zu und erzeugt
 * je Bezahl-Stufe einen gültigen Lizenzschlüssel (dieselbe Logik/Format,
 * die /api/license prüft). FREE, Zusatz-Dienste (Setup, Support) und der
 * Ultra-Levelup erzeugen KEINEN Lizenzschlüssel – FREE braucht keinen,
 * die anderen sind stufen-unabhängige Zusätze.
 *
 * Diese Datei ist bewusst frei von Seiteneffekten und einzeln testbar.
 */

import { generateLicenseKey, PAID_PLANS, type PaidPlan } from "./license";

export interface OrderLineItem {
  title?: string | null;
  quantity?: number | null;
}

export interface IssuedLicense {
  plan: PaidPlan;
  key: string;
}

/**
 * Bestimmt die Bezahl-Stufe aus einem Positions-Titel.
 * Beispiel-Titel: "PERSONAL AI – Ihr persönlicher KI-Assistent (Monatsabo)".
 * Gibt null zurück für FREE, Zusätze (Ultra/Setup/Support) und Unbekanntes.
 */
export function planFromTitle(title: string | null | undefined): PaidPlan | null {
  if (!title) return null;
  const t = title.toUpperCase();
  // Ultra-Levelup ist stufen-unabhängig -> hier kein Lizenzschlüssel.
  if (t.includes("ULTRA")) return null;
  for (const plan of PAID_PLANS) {
    // Wortgrenze, damit "PROFESSIONAL" nicht fälschlich "PERSONAL" trifft:
    // wir prüfen den Plan-Namen als eigenständiges Wort am Titelanfang.
    const re = new RegExp(`\\b${plan}\\b`);
    if (re.test(t)) return plan;
  }
  return null;
}

/**
 * Erzeugt für eine Bestellung die auszuliefernden Lizenzschlüssel –
 * einen pro Bezahl-Stufe (Menge wird berücksichtigt: 2x STARTER = 2 Keys).
 * Doppelte Stufen in mehreren Positionen werden zusammengezählt.
 */
export function licensesForOrder(lineItems: OrderLineItem[]): IssuedLicense[] {
  const out: IssuedLicense[] = [];
  for (const item of lineItems ?? []) {
    const plan = planFromTitle(item.title);
    if (!plan) continue;
    const menge = Math.max(1, Math.min(50, Math.floor(item.quantity ?? 1) || 1));
    for (let i = 0; i < menge; i++) {
      out.push({ plan, key: generateLicenseKey(plan) });
    }
  }
  return out;
}
