#!/usr/bin/env node
/**
 * Erzeugt Lizenzschluessel fuer den Verkauf (z. B. via Shopify).
 *
 *   node scripts/generate-license.mjs BUSINESS 5
 *   LICENSE_SECRET=... node scripts/generate-license.mjs STARTER
 *
 * Format: ACC-<PLAN>-<BASE32x16>-<HMAC8>
 * HMAC-SHA256 ueber "ACC-<PLAN>-<RANDOM>", erste 8 Hex-Zeichen (uppercase).
 * MUSS identisch zu lib/license.ts bleiben (Format + Fallback-Secret).
 */

import { createHmac, randomBytes } from "node:crypto";

const PLANS = ["STARTER", "PROFESSIONAL", "BUSINESS"];
const BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
const KEY_RANDOM_LENGTH = 16;

// WARNUNG: Fallback nur fuer die lokale Entwicklung – in Produktion
// LICENSE_SECRET setzen. Identische Konstante in lib/license.ts.
const DEV_FALLBACK_SECRET = "acc-dev-secret-nicht-fuer-produktion";

const [, , planArg, countArg] = process.argv;
const plan = (planArg ?? "").toUpperCase();

if (!PLANS.includes(plan)) {
  console.error(
    `Verwendung: node scripts/generate-license.mjs <${PLANS.join("|")}> [anzahl]`,
  );
  process.exit(1);
}

const count = countArg === undefined ? 1 : Number.parseInt(countArg, 10);
if (!Number.isInteger(count) || count < 1 || count > 1000) {
  console.error("Anzahl muss eine ganze Zahl zwischen 1 und 1000 sein.");
  process.exit(1);
}

const secret = process.env.LICENSE_SECRET || DEV_FALLBACK_SECRET;
if (!process.env.LICENSE_SECRET) {
  console.error(
    "WARNUNG: LICENSE_SECRET nicht gesetzt – Dev-Fallback-Secret aktiv. " +
      "Diese Schluessel NICHT verkaufen.",
  );
}

for (let i = 0; i < count; i++) {
  const bytes = randomBytes(KEY_RANDOM_LENGTH);
  let random = "";
  for (const b of bytes) random += BASE32_ALPHABET[b % 32];
  const payload = `ACC-${plan}-${random}`;
  const sig = createHmac("sha256", secret)
    .update(payload)
    .digest("hex")
    .slice(0, 8)
    .toUpperCase();
  console.log(`${payload}-${sig}`);
}
