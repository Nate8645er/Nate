/**
 * Tests für Kundenportal, Webhook-Signaturprüfung (Stripe) und Supabase-Login –
 * inkl. ehrlichem „nicht-konfiguriert" ohne Keys und echter HMAC-Verifikation.
 */
import { createHmac } from "node:crypto";
import { describe, expect, it } from "vitest";
import { billingPortalSessionErstellen, stripeWebhookVerifizieren } from "../lib/stripe";
import { supabaseKonfiguriert, anmelden, registrieren } from "../lib/supabase";

const SK = { STRIPE_SECRET_KEY: "sk_test_x" };

describe("Stripe Kundenportal", () => {
  it("ohne Key ehrlich nicht-konfiguriert", async () => {
    const r = await billingPortalSessionErstellen("cus_1", "https://x.ch", {});
    expect(r).toEqual({ error: "nicht-konfiguriert" });
  });
  it("ohne Customer-ID Fehler", async () => {
    const r = await billingPortalSessionErstellen("", "https://x.ch", SK);
    expect(r).toEqual({ error: "customer-fehlt" });
  });
  it("mit Key liefert Portal-URL und sendet Customer + Return-URL", async () => {
    let gesendet = "";
    const fakeFetch = (async (_u: string, init: RequestInit) => {
      gesendet = String(init.body);
      return { ok: true, json: async () => ({ url: "https://billing.stripe.com/p/abc" }) };
    }) as unknown as typeof fetch;
    const r = await billingPortalSessionErstellen("cus_42", "https://x.ch", SK, fakeFetch);
    expect(r).toEqual({ url: "https://billing.stripe.com/p/abc" });
    expect(gesendet).toContain("customer=cus_42");
    expect(gesendet).toContain("return_url=https%3A%2F%2Fx.ch%2Fkonto");
  });
});

describe("Stripe Webhook-Signatur", () => {
  const secret = "whsec_test";
  const payload = JSON.stringify({ type: "checkout.session.completed", data: { object: {} } });
  const t = 1_700_000_000;
  const gueltigeSig = createHmac("sha256", secret).update(`${t}.${payload}`).digest("hex");
  const header = `t=${t},v1=${gueltigeSig}`;

  it("akzeptiert gültige Signatur innerhalb der Toleranz", () => {
    expect(stripeWebhookVerifizieren(payload, header, secret, 300, t + 10)).toEqual({ ok: true });
  });
  it("ohne Secret: kein-secret", () => {
    expect(stripeWebhookVerifizieren(payload, header, undefined)).toEqual({ ok: false, grund: "kein-secret" });
  });
  it("ohne Header: kein-header", () => {
    expect(stripeWebhookVerifizieren(payload, null, secret)).toEqual({ ok: false, grund: "kein-header" });
  });
  it("kaputtes Format", () => {
    expect(stripeWebhookVerifizieren(payload, "unsinn", secret).ok).toBe(false);
  });
  it("veraltete Signatur (Replay-Schutz)", () => {
    expect(stripeWebhookVerifizieren(payload, header, secret, 300, t + 5000))
      .toEqual({ ok: false, grund: "veraltet" });
  });
  it("verändertes Payload => ungültig", () => {
    expect(stripeWebhookVerifizieren(payload + "x", header, secret, 300, t + 10))
      .toEqual({ ok: false, grund: "ungueltig" });
  });
});

describe("Supabase-Login", () => {
  const cfg = {
    NEXT_PUBLIC_SUPABASE_URL: "https://abcdefgh.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo.demo",
  };

  it("erkennt Konfiguration nur bei URL + Anon-Key", () => {
    expect(supabaseKonfiguriert({})).toBe(false);
    expect(supabaseKonfiguriert({ NEXT_PUBLIC_SUPABASE_URL: "https://x.supabase.co" })).toBe(false);
    expect(supabaseKonfiguriert(cfg)).toBe(true);
  });
  it("ohne Konfiguration ehrlich nicht-konfiguriert", async () => {
    const r = await anmelden("a@b.ch", "pw", {});
    expect(r).toEqual({ ok: false, error: "nicht-konfiguriert" });
  });
  it("leere Eingaben => ungueltige-daten", async () => {
    expect(await anmelden("", "", cfg)).toEqual({ ok: false, error: "ungueltige-daten" });
    expect(await registrieren("a@b.ch", "", cfg)).toEqual({ ok: false, error: "ungueltige-daten" });
  });
  it("erfolgreiche Anmeldung liefert Sitzung", async () => {
    let ziel = "";
    const fakeFetch = (async (u: string) => {
      ziel = u;
      return { ok: true, json: async () => ({ access_token: "at", refresh_token: "rt", user: { id: "u1", email: "a@b.ch" } }) };
    }) as unknown as typeof fetch;
    const r = await anmelden("a@b.ch", "pw", cfg, fakeFetch);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.sitzung.user).toEqual({ id: "u1", email: "a@b.ch" });
      expect(r.sitzung.access_token).toBe("at");
    }
    expect(ziel).toBe("https://abcdefgh.supabase.co/auth/v1/token?grant_type=password");
  });
  it("abgelehnte Anmeldung => auth-fehler mit Meldung", async () => {
    const fakeFetch = (async () => ({
      ok: false, json: async () => ({ msg: "Invalid login credentials" }),
    })) as unknown as typeof fetch;
    const r = await anmelden("a@b.ch", "falsch", cfg, fakeFetch);
    expect(r).toEqual({ ok: false, error: "auth-fehler", meldung: "Invalid login credentials" });
  });
});
