/**
 * Tests für den E-Mail-Versand (Resend) und die reine Willkommens-Mail-Vorlage.
 */
import { describe, expect, it } from "vitest";
import { mailKonfiguriert, sendeMail } from "../lib/mail";
import { willkommensMail } from "../lib/willkommen";

const CFG = { RESEND_API_KEY: "re_test_1234567890", MAIL_FROM: "shop@firma.ch" };

describe("mailKonfiguriert", () => {
  it("nur mit API-Key + gültigem Absender", () => {
    expect(mailKonfiguriert({})).toBe(false);
    expect(mailKonfiguriert({ RESEND_API_KEY: "re_x1234567890" })).toBe(false);
    expect(mailKonfiguriert({ RESEND_API_KEY: "re_x1234567890", MAIL_FROM: "kein-at" })).toBe(false);
    expect(mailKonfiguriert(CFG)).toBe(true);
  });
});

describe("sendeMail", () => {
  it("ohne Konfiguration ehrlich nicht-konfiguriert", async () => {
    expect(await sendeMail({ an: "a@b.ch", betreff: "x", text: "y" }, {})).toEqual({ ok: false, error: "nicht-konfiguriert" });
  });
  it("ungültige Empfänger/Felder", async () => {
    expect(await sendeMail({ an: "kein-at", betreff: "x", text: "y" }, CFG)).toEqual({ ok: false, error: "ungueltige-daten" });
    expect(await sendeMail({ an: "a@b.ch", betreff: "", text: "y" }, CFG)).toEqual({ ok: false, error: "ungueltige-daten" });
  });
  it("sendet an Resend mit Bearer + From/To", async () => {
    let url = "", init: RequestInit = {};
    const fakeFetch = (async (u: string, i: RequestInit) => {
      url = u; init = i;
      return { ok: true, json: async () => ({ id: "email_1" }) };
    }) as unknown as typeof fetch;
    const r = await sendeMail({ an: "kunde@x.ch", betreff: "Hallo", text: "Welt", html: "<b>Welt</b>" }, CFG, fakeFetch);
    expect(r).toEqual({ ok: true, id: "email_1" });
    expect(url).toBe("https://api.resend.com/emails");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer re_test_1234567890");
    const body = JSON.parse(String(init.body));
    expect(body).toMatchObject({ from: "shop@firma.ch", to: ["kunde@x.ch"], subject: "Hallo", text: "Welt", html: "<b>Welt</b>" });
  });
  it("Resend-Fehler wird gemeldet", async () => {
    const fakeFetch = (async () => ({ ok: false, json: async () => ({}) })) as unknown as typeof fetch;
    expect(await sendeMail({ an: "a@b.ch", betreff: "x", text: "y" }, CFG, fakeFetch)).toEqual({ ok: false, error: "mail-fehler" });
  });
});

describe("willkommensMail", () => {
  it("enthält Plan, Schlüssel und Einlöse-Link; escaped HTML", () => {
    const m = willkommensMail({
      an: "kunde@x.ch",
      planName: "Pro",
      lizenzSchluessel: "ACC-PROFESSIONAL-ABCDEFGHIJKLMNOP-1A2B3C4D",
      appUrl: "https://shop.ch/",
    });
    expect(m.an).toBe("kunde@x.ch");
    expect(m.betreff).toContain("Pro");
    expect(m.text).toContain("ACC-PROFESSIONAL-ABCDEFGHIJKLMNOP-1A2B3C4D");
    expect(m.text).toContain("https://shop.ch/onboarding");
    expect(m.html).toContain("ACC-PROFESSIONAL-ABCDEFGHIJKLMNOP-1A2B3C4D");
    // kein doppelter Slash im Link
    expect(m.text).not.toContain("shop.ch//onboarding");
  });
  it("escaped gefährliche Zeichen im Plannamen", () => {
    const m = willkommensMail({ an: "a@b.ch", planName: "<script>", lizenzSchluessel: "K", appUrl: "https://x.ch" });
    expect(m.html).not.toContain("<script>");
    expect(m.html).toContain("&lt;script&gt;");
  });
  it("ohne appUrl: kein Link, sondern Konto-Hinweis (kein Host-Header-Phishing)", () => {
    const m = willkommensMail({ an: "a@b.ch", planName: "Pro", lizenzSchluessel: "K" });
    expect(m.text).not.toContain("/onboarding");
    expect(m.text).toContain("Konto");
    expect(m.html).not.toContain("href=");
  });
  it("ignoriert nicht-https appUrl (kein unsicherer Link)", () => {
    const m = willkommensMail({ an: "a@b.ch", planName: "Pro", lizenzSchluessel: "K", appUrl: "http://evil.ch" });
    expect(m.html).not.toContain("href=");
  });
});
