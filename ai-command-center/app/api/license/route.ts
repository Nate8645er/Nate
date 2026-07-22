/**
 * POST /api/license
 *
 * Nimmt { key: string } entgegen, prüft den Lizenzschlüssel
 * (HMAC, lib/license.ts) und gibt bei Erfolg
 * { valid: true, plan, token, expiresAt } zurück.
 * Das Token (30 Tage gültig) hält der Client in localStorage und
 * sendet es bei POST /api/mission als Header "x-acc-license" mit.
 */

import {
  createLicenseToken,
  createUltraToken,
  verifyLicenseKey,
  verifyUltraKey,
} from "@/lib/license";

export const runtime = "nodejs";

const MAX_KEY_LENGTH = 100;

export async function POST(request: Request): Promise<Response> {
  let key: unknown;
  try {
    const body: unknown = await request.json();
    key = (body as { key?: unknown })?.key;
  } catch {
    return jsonError("Ungültiger Request-Body (JSON erwartet).", 400);
  }

  if (typeof key !== "string" || !key.trim()) {
    return jsonError('Feld "key" (nicht-leerer String) ist erforderlich.', 400);
  }
  if (key.length > MAX_KEY_LENGTH) {
    return jsonError("Ungültiger Lizenzschlüssel.", 401);
  }

  // Ultra-Levelup-Codes ("ACC-ULTRA-…") werden über dieselbe Eingabe
  // eingelöst und liefern ein eigenes Token (Header "x-acc-ultra").
  const ultra = verifyUltraKey(key);
  if (ultra.valid) {
    const { token, expiresAt } = createUltraToken(ultra.plan);
    return Response.json({
      valid: true,
      ultra: true,
      plan: ultra.plan,
      token,
      expiresAt,
    });
  }

  const result = verifyLicenseKey(key);
  if (!result.valid) {
    return Response.json(
      { valid: false, error: "Ungültiger Lizenzschlüssel." },
      { status: 401 },
    );
  }

  const { token, expiresAt } = createLicenseToken(result.plan);
  return Response.json({ valid: true, plan: result.plan, token, expiresAt });
}

function jsonError(message: string, status: number): Response {
  return Response.json({ valid: false, error: message }, { status });
}
