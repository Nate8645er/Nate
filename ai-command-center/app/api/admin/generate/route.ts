/**
 * POST /api/admin/generate
 *
 * Interne Admin-Route zum Erzeugen von Lizenzschlüsseln per Klick
 * (Ersatz für scripts/generate-license.mjs auf der Kommandozeile).
 *
 * Body: { password: string, plan: PaidPlan, count: number, ultra?: boolean }
 * ultra:true erzeugt Ultra-Levelup-Codes (ACC-ULTRA-<PLAN>-...) statt Lizenzen.
 *
 * Auth: Das Passwort wird timing-sicher mit process.env.ADMIN_SECRET
 * verglichen. Ist ADMIN_SECRET nicht gesetzt, dient das Signatur-Secret
 * der Lizenzen (LICENSE_SECRET, sonst Dev-Fallback) als Passwort – so
 * funktioniert die Seite ohne Zusatz-Konfiguration. Bei falschem Passwort
 * antwortet die Route generisch mit 401 (kein Hinweis auf das Secret).
 *
 * Die Schlüssel werden mit generateLicenseKey() aus lib/license.ts
 * erzeugt – dieselbe Logik/Format wie /api/license sie prüft. Antwort:
 * { keys: string[] }.
 */

import { createHash, timingSafeEqual } from "node:crypto";
import { generateLicenseKey, generateUltraKey, licenseSecret, PAID_PLANS, type PaidPlan } from "@/lib/license";

export const runtime = "nodejs";

const MAX_COUNT = 50;
const MIN_COUNT = 1;
const MAX_PASSWORD_LENGTH = 512;

/**
 * Timing-sicherer Passwort-Vergleich für beliebig lange Eingaben:
 * beide Seiten werden zuerst auf einen SHA-256-Digest fester Länge
 * abgebildet, sodass timingSafeEqual keine Längen-Info preisgibt.
 */
function passwordMatches(provided: string, expected: string): boolean {
  const a = createHash("sha256").update(provided, "utf8").digest();
  const b = createHash("sha256").update(expected, "utf8").digest();
  return timingSafeEqual(a, b);
}

/** Das erwartete Admin-Passwort: ADMIN_SECRET, sonst das Lizenz-Secret. */
function adminSecret(): string {
  const admin = process.env.ADMIN_SECRET;
  if (admin && admin.length > 0) return admin;
  return licenseSecret();
}

function jsonError(message: string, status: number): Response {
  return Response.json({ error: message }, { status });
}

export async function POST(request: Request): Promise<Response> {
  let body: { password?: unknown; plan?: unknown; count?: unknown };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return jsonError("Ungültiger Request-Body (JSON erwartet).", 400);
  }

  const { password, plan, count } = body;
  const ultra = (body as { ultra?: unknown }).ultra === true;

  if (typeof password !== "string" || !password) {
    return jsonError('Feld "password" ist erforderlich.', 400);
  }
  if (password.length > MAX_PASSWORD_LENGTH) {
    // Ueberlanges Passwort ist immer falsch – generische Meldung.
    return jsonError("Falsches Passwort.", 401);
  }

  // Auth zuerst prüfen, damit ungültige Eingaben nichts über die
  // Existenz/Gültigkeit von Plan/Anzahl verraten.
  let expected: string;
  try {
    expected = adminSecret();
  } catch {
    // In Produktion ohne LICENSE_SECRET und ohne ADMIN_SECRET: nicht nutzbar.
    return jsonError("Admin-Zugang ist auf diesem Server nicht konfiguriert.", 503);
  }
  if (!passwordMatches(password, expected)) {
    return jsonError("Falsches Passwort.", 401);
  }

  if (typeof plan !== "string" || !(PAID_PLANS as readonly string[]).includes(plan)) {
    return jsonError(
      `Ungültiger Plan. Erlaubt: ${PAID_PLANS.join(", ")}.`,
      400,
    );
  }

  // count 1..50 clampen; ungültige/fehlende Angabe => 1.
  const parsedCount =
    typeof count === "number" && Number.isFinite(count) ? Math.floor(count) : 1;
  const clampedCount = Math.min(MAX_COUNT, Math.max(MIN_COUNT, parsedCount));

  const keys: string[] = [];
  for (let i = 0; i < clampedCount; i++) {
    keys.push(
      ultra ? generateUltraKey(plan as PaidPlan) : generateLicenseKey(plan as PaidPlan),
    );
  }

  return Response.json({ keys });
}
