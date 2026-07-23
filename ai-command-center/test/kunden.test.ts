/**
 * Tests für Kunden-/Abo-Speicher (Supabase PostgREST), Webhook-Event-Deutung
 * und Sitzungs-Lookup – inkl. ehrlichem „nicht-konfiguriert" ohne Service-Key.
 */
import { describe, expect, it } from "vitest";
import {
  kundenStoreKonfiguriert,
  aboFreischalten,
  aboLesen,
  customerIdFuerEmail,
} from "../lib/kunden";
import { webhookEreignisDeuten } from "../lib/stripe";
import { sitzungBenutzer } from "../lib/supabase";

const CFG = {
  NEXT_PUBLIC_SUPABASE_URL: "https://abcdefgh.supabase.co",
  SUPABASE_SERVICE_ROLE_KEY: "service_role_key_das_lang_genug_ist_xxxxxx",
};

describe("Kunden-Store Konfiguration", () => {
  it("nur mit URL + Service-Role-Key konfiguriert", () => {
    expect(kundenStoreKonfiguriert({})).toBe(false);
    expect(kundenStoreKonfiguriert({ NEXT_PUBLIC_SUPABASE_URL: CFG.NEXT_PUBLIC_SUPABASE_URL })).toBe(false);
    expect(kundenStoreKonfiguriert(CFG)).toBe(true);
  });
  it("ohne Konfiguration ehrlich nicht-konfiguriert", async () => {
    const r = await aboFreischalten({ customer_id: "cus_1", email: "a@b.ch", plan_id: "pro", status: "active" }, {});
    expect(r).toEqual({ ok: false, error: "nicht-konfiguriert" });
  });
});

describe("aboFreischalten (Upsert)", () => {
  it("sendet Upsert mit merge-duplicates an /abos", async () => {
    let url = "", init: RequestInit = {};
    const fakeFetch = (async (u: string, i: RequestInit) => {
      url = u; init = i;
      return { ok: true, json: async () => ({}) };
    }) as unknown as typeof fetch;
    const r = await aboFreischalten(
      { customer_id: "cus_9", email: "k@firma.ch", plan_id: "pro", status: "active" },
      CFG,
      fakeFetch,
    );
    expect(r).toEqual({ ok: true });
    expect(url).toBe("https://abcdefgh.supabase.co/rest/v1/abos?on_conflict=customer_id");
    expect((init.headers as Record<string, string>).Prefer).toContain("merge-duplicates");
    expect(String(init.body)).toContain("cus_9");
  });
  it("fehlende Pflichtfelder => ungueltige-daten", async () => {
    const r = await aboFreischalten({ customer_id: "", email: null, plan_id: "", status: "active" }, CFG);
    expect(r).toEqual({ ok: false, error: "ungueltige-daten" });
  });
  it("DB-Fehler wird sauber gemeldet", async () => {
    const fakeFetch = (async () => ({ ok: false, json: async () => ({}) })) as unknown as typeof fetch;
    const r = await aboFreischalten({ customer_id: "c", email: null, plan_id: "pro", status: "active" }, CFG, fakeFetch);
    expect(r).toEqual({ ok: false, error: "db-fehler" });
  });
});

describe("aboLesen & customerIdFuerEmail", () => {
  it("liest Abo zu customerId", async () => {
    const fakeFetch = (async (u: string) => {
      expect(u).toContain("customer_id=eq.cus_5");
      return { ok: true, json: async () => [{ customer_id: "cus_5", email: "x@y.ch", plan_id: "start", status: "active" }] };
    }) as unknown as typeof fetch;
    const abo = await aboLesen("cus_5", CFG, fakeFetch);
    expect(abo?.plan_id).toBe("start");
  });
  it("customerId per E-Mail (neuestes zuerst)", async () => {
    const fakeFetch = (async (u: string) => {
      expect(u).toContain("email=eq.");
      expect(u).toContain("order=aktualisiert_am.desc");
      return { ok: true, json: async () => [{ customer_id: "cus_neu", email: "a@b.ch", plan_id: "pro", status: "active" }] };
    }) as unknown as typeof fetch;
    expect(await customerIdFuerEmail("a@b.ch", CFG, fakeFetch)).toBe("cus_neu");
  });
  it("keine Treffer => null", async () => {
    const fakeFetch = (async () => ({ ok: true, json: async () => [] })) as unknown as typeof fetch;
    expect(await aboLesen("cus_x", CFG, fakeFetch)).toBeNull();
    expect(await customerIdFuerEmail("nix@x.ch", CFG, fakeFetch)).toBeNull();
  });
});

describe("webhookEreignisDeuten", () => {
  it("checkout.session.completed → customerId/planId/email/status/eventZeit", () => {
    const abo = webhookEreignisDeuten({
      type: "checkout.session.completed",
      created: 1700,
      data: { object: { customer: "cus_1", customer_details: { email: "k@f.ch" }, metadata: { planId: "PROFESSIONAL" } } },
    });
    expect(abo).toEqual({ customerId: "cus_1", email: "k@f.ch", planId: "PROFESSIONAL", status: "active", eventZeit: 1700 });
  });
  it("subscription.deleted → status canceled", () => {
    const abo = webhookEreignisDeuten({
      type: "customer.subscription.deleted",
      data: { object: { customer: "cus_2", status: "active", metadata: { planId: "STARTER" } } },
    });
    expect(abo?.status).toBe("canceled");
  });
  it("irrelevanter Typ => null", () => {
    expect(webhookEreignisDeuten({ type: "invoice.paid", data: { object: { customer: "cus_3" } } })).toBeNull();
  });
  it("ohne customerId/planId => null", () => {
    expect(webhookEreignisDeuten({ type: "checkout.session.completed", data: { object: { metadata: {} } } })).toBeNull();
  });
  it("unbekannte planId => null (Defense-in-Depth)", () => {
    expect(webhookEreignisDeuten({
      type: "checkout.session.completed",
      data: { object: { customer: "cus_4", metadata: { planId: "HACKER_PLAN" } } },
    })).toBeNull();
  });
});

describe("aboFreischalten Reihenfolge-Schutz", () => {
  it("verwirft veraltetes Ereignis (älter als gespeicherter Stand)", async () => {
    const fakeFetch = (async (u: string) => {
      // Nur der Lese-Aufruf wird erwartet; ein Schreibaufruf wäre ein Fehler.
      expect(u).toContain("customer_id=eq.cus_r");
      return { ok: true, json: async () => [{ customer_id: "cus_r", email: null, plan_id: "pro", status: "canceled", event_zeit: 2000 }] };
    }) as unknown as typeof fetch;
    const r = await aboFreischalten(
      { customer_id: "cus_r", email: null, plan_id: "pro", status: "active", event_zeit: 1000 },
      CFG, fakeFetch,
    );
    expect(r).toEqual({ ok: false, error: "veraltet" });
  });
  it("wendet neueres Ereignis an", async () => {
    let geschrieben = false;
    const fakeFetch = (async (u: string, i?: RequestInit) => {
      if (i?.method === "POST") { geschrieben = true; return { ok: true, json: async () => ({}) }; }
      return { ok: true, json: async () => [{ customer_id: "cus_r", email: null, plan_id: "pro", status: "active", event_zeit: 1000 }] };
    }) as unknown as typeof fetch;
    const r = await aboFreischalten(
      { customer_id: "cus_r", email: null, plan_id: "pro", status: "canceled", event_zeit: 3000 },
      CFG, fakeFetch,
    );
    expect(r).toEqual({ ok: true });
    expect(geschrieben).toBe(true);
  });
});

describe("sitzungBenutzer", () => {
  const SB = {
    NEXT_PUBLIC_SUPABASE_URL: "https://abcdefgh.supabase.co",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.demo.demo",
  };
  it("ohne Token null", async () => {
    expect(await sitzungBenutzer(undefined, SB)).toBeNull();
  });
  it("gültiges Refresh-Token mit bestätigter E-Mail → Benutzer", async () => {
    const fakeFetch = (async (u: string) => {
      expect(u).toContain("grant_type=refresh_token");
      return { ok: true, json: async () => ({ access_token: "at", refresh_token: "rt2", user: { id: "u9", email: "a@b.ch", email_confirmed_at: "2026-01-01T00:00:00Z" } }) };
    }) as unknown as typeof fetch;
    const u = await sitzungBenutzer("rt", SB, fakeFetch);
    expect(u).toEqual({ id: "u9", email: "a@b.ch", emailBestaetigt: true });
  });
  it("unbestätigte E-Mail → null (Schutz gegen Konto-Übernahme)", async () => {
    const fakeFetch = (async () => ({
      ok: true, json: async () => ({ access_token: "at", refresh_token: "rt2", user: { id: "u9", email: "opfer@b.ch" } }),
    })) as unknown as typeof fetch;
    expect(await sitzungBenutzer("rt", SB, fakeFetch)).toBeNull();
  });
  it("abgelaufenes Token → null", async () => {
    const fakeFetch = (async () => ({ ok: false, json: async () => ({ msg: "expired" }) })) as unknown as typeof fetch;
    expect(await sitzungBenutzer("alt", SB, fakeFetch)).toBeNull();
  });
});
