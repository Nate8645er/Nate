/**
 * Stateless Lizenz- & Usage-System (HMAC-SHA256, ohne Datenbank).
 *
 * Drei Artefakte, alle mit demselben Secret signiert:
 *
 * 1. LIZENZSCHLUESSEL  "ACC-<PLAN>-<BASE32RANDOM>-<HMAC8>"
 *    HMAC-SHA256 über "ACC-<PLAN>-<RANDOM>", erste 8 Hex-Zeichen
 *    (uppercase). Wird verkauft (Shopify) und einmalig gegen ein
 *    Lizenz-Token eingetauscht (POST /api/license).
 *
 * 2. LIZENZ-TOKEN  base64url(JSON{p,exp}) + "." + HMAC-Hex
 *    30 Tage gültig, liegt im localStorage des Clients und wird als
 *    Header "x-acc-license" mitgesendet. Ungültig/abgelaufen => FREE.
 *
 * 3. USAGE-TOKEN  base64url(JSON{d,u}) + "." + HMAC-Hex
 *    Stateless Tageszähler (UTC-Datum + verbrauchte Missionen).
 *    Der Server signiert ihn bei jeder Antwort neu (SSE-Event "usage"),
 *    der Client sendet ihn als Header "x-acc-usage" zurück.
 *    Manipulation fällt durch die HMAC-Prüfung auf => Zähler 0,
 *    aber der Plan bleibt durch das Lizenz-Token begrenzt.
 *
 * Grenze des Ansatzes (bewusst akzeptiert, Vercel-tauglich ohne DB):
 * Ein Client, der sein Usage-Token verwirft, beginnt den Tag bei 0.
 *
 * Die Schlüssel-Logik ist in scripts/generate-license.mjs dupliziert –
 * Aenderungen an Format oder Fallback-Secret dort nachziehen.
 */

import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import type { PlanId } from "./agents/types";

/** Bezahlte Pläne, für die Schlüssel verkauft werden. */
export type PaidPlan = Exclude<PlanId, "FREE">;
export const PAID_PLANS: readonly PaidPlan[] = [
  "PERSONAL",
  "STARTER",
  "PROFESSIONAL",
  "BUSINESS",
  "ENTERPRISE",
] as const;

/** Missionen pro Kalendertag (UTC) – wird SERVERSEITIG erzwungen. */
export const PLAN_LIMITS: Record<PlanId, number> = {
  FREE: 3,
  PERSONAL: 10,
  STARTER: 25,
  PROFESSIONAL: 100,
  BUSINESS: 400,
  ENTERPRISE: 1000,
};

/**
 * Token-Budget pro KI-Antwort (max_tokens je LLM-Call) – wird
 * SERVERSEITIG erzwungen. FREE ist bewusst knapp gehalten: zum
 * Kennenlernen reicht es, für ernsthafte Arbeit lohnt das Upgrade.
 */
export const TOKEN_BUDGET: Record<PlanId, number> = {
  FREE: 700,
  PERSONAL: 1400,
  STARTER: 2000,
  PROFESSIONAL: 2800,
  BUSINESS: 3600,
  ENTERPRISE: 4096,
};

/** Ultra-Levelup: Faktor auf Missionen/Tag und Token-Budget. */
export const ULTRA_FAKTOR = 1.5;
/** Ultra-Levelup: zusätzliche Web-Quellen für den KI-Browser. */
export const ULTRA_EXTRA_QUELLEN = 2;

/** Effektives Tageslimit (Ultra hebt es um den Faktor an). */
export function effektivesLimit(plan: PlanId, ultra: boolean): number {
  return ultra ? Math.ceil(PLAN_LIMITS[plan] * ULTRA_FAKTOR) : PLAN_LIMITS[plan];
}

/** Effektives Token-Budget pro Antwort. */
export function effektivesTokenBudget(plan: PlanId, ultra: boolean): number {
  return ultra
    ? Math.min(4096, Math.ceil(TOKEN_BUDGET[plan] * ULTRA_FAKTOR))
    : TOKEN_BUDGET[plan];
}

/** Nächsthöherer Plan für die Upgrade-Empfehlung im Limit-Fehler. */
const NEXT_PLAN: Record<PlanId, PaidPlan | null> = {
  FREE: "PERSONAL",
  PERSONAL: "STARTER",
  STARTER: "PROFESSIONAL",
  PROFESSIONAL: "BUSINESS",
  BUSINESS: "ENTERPRISE",
  ENTERPRISE: null,
};

/** Lizenz-Token-Laufzeit: 30 Tage. */
const LICENSE_TOKEN_TTL_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * WARNUNG: Fallback-Secret NUR für die lokale Entwicklung.
 * In Produktion MUSS process.env.LICENSE_SECRET gesetzt sein, sonst
 * kann jeder mit Quellcode-Zugriff gültige Schlüssel/Token erzeugen.
 * (Identische Konstante in scripts/generate-license.mjs.)
 */
const DEV_FALLBACK_SECRET = "acc-dev-secret-nicht-für-produktion";

/**
 * Liefert das aktive Signatur-Secret (LICENSE_SECRET, sonst Dev-Fallback).
 * Wird ausser für die HMAC-Signatur auch von der Admin-Route als Fallback
 * für die Passwort-Prüfung genutzt (POST /api/admin/generate).
 */
export function licenseSecret(): string {
  const s = process.env.LICENSE_SECRET;
  if (!s) {
    if (process.env.NODE_ENV === "production") {
      throw new Error(
        "LICENSE_SECRET ist nicht gesetzt. In Produktion ist der Betrieb ohne eigenes Secret nicht erlaubt.",
      );
    }
    return DEV_FALLBACK_SECRET;
  }
  return s;
}

/* ------------------------------ HMAC-Helfer ------------------------------- */

function hmacHex(data: string): string {
  return createHmac("sha256", licenseSecret()).update(data).digest("hex");
}

/** Timing-sicherer Vergleich zweier Hex-/ASCII-Strings. */
function safeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a, "utf8");
  const bufB = Buffer.from(b, "utf8");
  return bufA.length === bufB.length && timingSafeEqual(bufA, bufB);
}

/** Signiert ein JSON-Payload als "base64url(JSON).hmacHex". */
function signToken(payload: Record<string, unknown>): string {
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${body}.${hmacHex(body)}`;
}

/** Liest ein signiertes Token; null bei falscher Signatur/Format. */
function readToken(token: string): Record<string, unknown> | null {
  const dot = token.lastIndexOf(".");
  if (dot <= 0) return null;
  const body = token.slice(0, dot);
  const sig = token.slice(dot + 1);
  if (!safeEqual(hmacHex(body), sig)) return null;
  try {
    const parsed: unknown = JSON.parse(
      Buffer.from(body, "base64url").toString("utf8"),
    );
    return typeof parsed === "object" && parsed !== null
      ? (parsed as Record<string, unknown>)
      : null;
  } catch {
    return null;
  }
}

/* ---------------------------- Lizenzschlüssel ---------------------------- */

const BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
const KEY_RANDOM_LENGTH = 16;
const KEY_RE = /^ACC-(PERSONAL|STARTER|PROFESSIONAL|BUSINESS|ENTERPRISE)-([A-Z2-7]{16})-([0-9A-F]{8})$/;

function keySignature(payload: string): string {
  return hmacHex(payload).slice(0, 8).toUpperCase();
}

/** Erzeugt einen neuen Schlüssel "ACC-<PLAN>-<BASE32x16>-<HMAC8>". */
export function generateLicenseKey(plan: PaidPlan): string {
  const bytes = randomBytes(KEY_RANDOM_LENGTH);
  let random = "";
  for (const b of bytes) random += BASE32_ALPHABET[b % 32];
  const payload = `ACC-${plan}-${random}`;
  return `${payload}-${keySignature(payload)}`;
}

/** Prüft einen Schlüssel; bei Erfolg inkl. Plan. */
export function verifyLicenseKey(
  key: string,
): { valid: true; plan: PaidPlan } | { valid: false } {
  const match = KEY_RE.exec(key.trim().toUpperCase());
  if (!match) return { valid: false };
  const [, plan, random, sig] = match;
  if (!safeEqual(keySignature(`ACC-${plan}-${random}`), sig)) {
    return { valid: false };
  }
  return { valid: true, plan: plan as PaidPlan };
}

/* --------------------------- Ultra-Levelup-Codes -------------------------- */

/**
 * Ultra-Levelup-Codes "ACC-ULTRA-<PLAN>-<BASE32x16>-<HMAC8>" – nur für
 * bezahlte Pläne. Ein Ultra-Code wird ZUSÄTZLICH zur Lizenz aktiviert
 * und hebt genau diese Stufe an: +50% Missionen/Tag, +50% Token-Budget,
 * +2 Browser-Quellen und die Skills der nächsthöheren Stufe.
 */
const ULTRA_KEY_RE =
  /^ACC-ULTRA-(PERSONAL|STARTER|PROFESSIONAL|BUSINESS|ENTERPRISE)-([A-Z2-7]{16})-([0-9A-F]{8})$/;

/** Erzeugt einen Ultra-Levelup-Code für die angegebene Bezahl-Stufe. */
export function generateUltraKey(plan: PaidPlan): string {
  const bytes = randomBytes(KEY_RANDOM_LENGTH);
  let random = "";
  for (const b of bytes) random += BASE32_ALPHABET[b % 32];
  const payload = `ACC-ULTRA-${plan}-${random}`;
  return `${payload}-${keySignature(payload)}`;
}

/** Prüft einen Ultra-Code; bei Erfolg inkl. Stufe, für die er gilt. */
export function verifyUltraKey(
  key: string,
): { valid: true; plan: PaidPlan } | { valid: false } {
  const match = ULTRA_KEY_RE.exec(key.trim().toUpperCase());
  if (!match) return { valid: false };
  const [, plan, random, sig] = match;
  if (!safeEqual(keySignature(`ACC-ULTRA-${plan}-${random}`), sig)) {
    return { valid: false };
  }
  return { valid: true, plan: plan as PaidPlan };
}

/** Erzeugt ein 30 Tage gültiges Ultra-Token (Header "x-acc-ultra"). */
export function createUltraToken(plan: PaidPlan): {
  token: string;
  expiresAt: string;
} {
  const exp = Date.now() + LICENSE_TOKEN_TTL_MS;
  return {
    token: signToken({ ul: plan, exp }),
    expiresAt: new Date(exp).toISOString(),
  };
}

/**
 * Ist für den aktiven Plan ein gültiges Ultra-Token vorhanden?
 * Das Ultra-Token zählt nur, wenn es zur Stufe des Lizenz-Tokens passt –
 * ein PERSONAL-Ultra-Code wertet keinen STARTER auf.
 */
export function ultraAktiv(token: string | null, plan: PlanId): boolean {
  if (!token || plan === "FREE") return false;
  const payload = readToken(token);
  if (!payload) return false;
  return (
    payload.ul === plan &&
    typeof payload.exp === "number" &&
    payload.exp > Date.now()
  );
}

/* ------------------------------ Lizenz-Token ------------------------------ */

/** Erzeugt ein 30 Tage gültiges, signiertes Lizenz-Token. */
export function createLicenseToken(plan: PaidPlan): {
  token: string;
  expiresAt: string;
} {
  const exp = Date.now() + LICENSE_TOKEN_TTL_MS;
  return {
    token: signToken({ p: plan, exp }),
    expiresAt: new Date(exp).toISOString(),
  };
}

/**
 * Ermittelt den Plan aus dem "x-acc-license"-Header.
 * Fehlend, manipuliert oder abgelaufen => FREE.
 */
export function planFromLicenseToken(token: string | null): PlanId {
  if (!token) return "FREE";
  const payload = readToken(token);
  if (!payload) return "FREE";
  const plan = payload.p;
  const exp = payload.exp;
  if (
    typeof plan !== "string" ||
    !(PAID_PLANS as readonly string[]).includes(plan) ||
    typeof exp !== "number" ||
    exp <= Date.now()
  ) {
    return "FREE";
  }
  return plan as PaidPlan;
}

/* ------------------------------- Usage-Token ------------------------------ */

export interface UsageDecision {
  /** false => Tageslimit erreicht, Mission NICHT starten. */
  allowed: boolean;
  /** Zählerstand nach dieser Entscheidung (inkl. der neuen Mission). */
  used: number;
  limit: number;
  /** Neu signiertes Token für den Client. */
  token: string;
  /** Deutsche Fehlermeldung, wenn nicht erlaubt. */
  message?: string;
}

/** Aktuelles UTC-Datum als "YYYY-MM-DD" (Zähl-Periode). */
function todayUtc(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Prüft das Usage-Token gegen das Tageslimit des Plans und verbraucht
 * bei Erfolg eine Mission. Manipulierte/fremde/veraltete Token zählen
 * als 0 (neuer Tag).
 */
export function consumeUsage(
  usageToken: string | null,
  plan: PlanId,
  ultra = false,
): UsageDecision {
  const today = todayUtc();
  const limit = effektivesLimit(plan, ultra);

  let used = 0;
  if (usageToken) {
    const payload = readToken(usageToken);
    if (
      payload &&
      payload.d === today &&
      typeof payload.u === "number" &&
      Number.isInteger(payload.u) &&
      payload.u > 0
    ) {
      used = payload.u;
    }
  }

  if (used >= limit) {
    const next = NEXT_PLAN[plan];
    const message = next
      ? `Tageslimit erreicht (${limit} Missionen/Tag im Plan ${plan}) – Upgrade auf ${next} für ${PLAN_LIMITS[next]} Missionen/Tag.`
      : `Tageslimit erreicht (${limit} Missionen/Tag im Plan ${plan}) – morgen geht es weiter.`;
    return {
      allowed: false,
      used,
      limit,
      token: signToken({ d: today, u: used }),
      message,
    };
  }

  const nextUsed = used + 1;
  return {
    allowed: true,
    used: nextUsed,
    limit,
    token: signToken({ d: today, u: nextUsed }),
  };
}
