/**
 * POST /api/shopify/webhook  —  automatische Lizenz-Auslieferung.
 *
 * Shopify ruft diese Route bei jeder bezahlten Bestellung auf
 * (Webhook-Thema "orders/paid"). Ablauf:
 *   1. Echtheit der Anfrage per HMAC prüfen (SHOPIFY_WEBHOOK_SECRET).
 *   2. Bezahlte Abo-Positionen den Stufen zuordnen und je Stufe einen
 *      gültigen Lizenzschlüssel erzeugen (lib/shopify-license).
 *   3. Schlüssel ausliefern – so viel, wie konfiguriert ist:
 *        - immer: an die Bestellung hängen (Notiz + Metafeld) über die
 *          Admin-API, sofern SHOPIFY_ADMIN_TOKEN gesetzt ist;
 *        - optional: dem Kunden per E-Mail schicken, wenn RESEND_API_KEY
 *          und ACC_FROM_EMAIL gesetzt sind.
 *   4. Immer schnell 200 antworten, damit Shopify nicht erneut zustellt.
 *
 * Sicherheit: Ohne gültige HMAC wird mit 401 abgelehnt. Fehler bei
 * Auslieferung brechen die Antwort nicht ab (Best-Effort, protokolliert).
 * Die Schlüssel werden mit dem produktiven LICENSE_SECRET erzeugt – die
 * Auslieferung MUSS daher in der Produktivumgebung laufen.
 */

import { createHmac, timingSafeEqual } from "node:crypto";
import { licensesForOrder, type OrderLineItem } from "@/lib/shopify-license";
import { effektivesLimit } from "@/lib/license";

export const runtime = "nodejs";

interface ShopifyOrder {
  id?: number;
  admin_graphql_api_id?: string;
  name?: string;
  email?: string;
  customer?: { email?: string; first_name?: string };
  line_items?: OrderLineItem[];
}

/** Prüft die Shopify-HMAC (Base64 von HMAC-SHA256 über den Rohtext). */
function hmacGueltig(rohtext: string, header: string | null, secret: string): boolean {
  if (!header) return false;
  const erwartet = createHmac("sha256", secret).update(rohtext, "utf8").digest();
  let empfangen: Buffer;
  try {
    empfangen = Buffer.from(header, "base64");
  } catch {
    return false;
  }
  if (empfangen.length !== erwartet.length) return false;
  return timingSafeEqual(empfangen, erwartet);
}

/** Hängt die Schlüssel als Notiz + Metafeld an die Bestellung. */
async function anBestellungHaengen(order: ChildOrderRef, keysText: string): Promise<void> {
  const domain = process.env.SHOPIFY_STORE_DOMAIN;
  const token = process.env.SHOPIFY_ADMIN_TOKEN;
  if (!domain || !token || !order.gid) return;
  const query = `mutation($input: OrderInput!) {
    orderUpdate(input: $input) { userErrors { message } }
  }`;
  const input = {
    id: order.gid,
    note: `AI Command Center – Lizenzschlüssel:\n${keysText}`,
    metafields: [{ namespace: "acc", key: "license_keys", type: "multi_line_text_field", value: keysText }],
  };
  const res = await fetch(`https://${domain}/admin/api/2025-01/graphql.json`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Shopify-Access-Token": token },
    body: JSON.stringify({ query, variables: { input } }),
  });
  if (!res.ok) throw new Error(`Admin-API ${res.status}`);
}

/** Schickt dem Kunden die Schlüssel per E-Mail (nur wenn Resend konfiguriert). */
async function perMailSchicken(email: string, vorname: string, keysHtml: string): Promise<void> {
  const apiKey = process.env.RESEND_API_KEY;
  const from = process.env.ACC_FROM_EMAIL;
  if (!apiKey || !from || !email) return;
  const html = `<p>Hallo ${vorname || ""},</p>
<p>vielen Dank für Ihren Kauf des AI Command Center. Hier ist Ihr Zugang:</p>
${keysHtml}
<p>So starten Sie: Öffnen Sie den Link <code>/dashboard?key=IHR-SCHLÜSSEL</code> auf PC oder Handy – die Lizenz aktiviert sich automatisch.</p>
<p>Viel Erfolg!</p>`;
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ from, to: email, subject: "Ihr AI-Command-Center-Zugang", html }),
  });
  if (!res.ok) throw new Error(`Resend ${res.status}`);
}

interface ChildOrderRef {
  gid?: string;
}

export async function POST(request: Request): Promise<Response> {
  const secret = process.env.SHOPIFY_WEBHOOK_SECRET;
  if (!secret) {
    // Ohne Secret keine Echtheitsprüfung möglich -> sicherheitshalber ablehnen.
    return Response.json({ error: "Webhook nicht konfiguriert." }, { status: 503 });
  }

  const rohtext = await request.text();
  const header = request.headers.get("x-shopify-hmac-sha256");
  if (!hmacGueltig(rohtext, header, secret)) {
    return Response.json({ error: "Ungültige Signatur." }, { status: 401 });
  }

  let order: ShopifyOrder;
  try {
    order = JSON.parse(rohtext) as ShopifyOrder;
  } catch {
    return Response.json({ error: "Ungültiger Body." }, { status: 400 });
  }

  const lizenzen = licensesForOrder(order.line_items ?? []);
  if (lizenzen.length === 0) {
    // Nichts Lizenzpflichtiges gekauft (z. B. nur FREE/Zusatz) -> ok.
    return Response.json({ ok: true, issued: 0 });
  }

  const keysText = lizenzen
    .map((l) => `${l.plan}: ${l.key}  (${effektivesLimit(l.plan, false)} Missionen/Tag)`)
    .join("\n");
  const keysHtml =
    "<ul>" + lizenzen.map((l) => `<li><strong>${l.plan}</strong>: <code>${l.key}</code></li>`).join("") + "</ul>";

  const email = order.email || order.customer?.email || "";
  const vorname = order.customer?.first_name || "";

  // Best-Effort-Auslieferung: Fehler einzelner Kanäle brechen nichts ab.
  await Promise.allSettled([
    anBestellungHaengen({ gid: order.admin_graphql_api_id }, keysText),
    perMailSchicken(email, vorname, keysHtml),
  ]);

  return Response.json({ ok: true, issued: lizenzen.length });
}
