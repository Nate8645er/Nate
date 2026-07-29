/**
 * Tests der Integrations-Schicht: Register-Konsistenz, Stufen-Gating und
 * Status-/Health-Logik (inkl. ehrlichem „nicht-konfiguriert").
 */
import { describe, expect, it } from "vitest";
import {
  INTEGRATIONS,
  STUFEN,
  integrationById,
  integrationsFuerStufe,
} from "../lib/integrations/registry";
import {
  grundStatus,
  healthUrl,
  istKonfiguriert,
  pingIntegration,
} from "../lib/integrations/status";

describe("Integrations-Register", () => {
  it("hat eindeutige IDs und gültige Felder", () => {
    const ids = INTEGRATIONS.map((i) => i.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const i of INTEGRATIONS) {
      expect(i.name).toBeTruthy();
      expect(i.repo).toMatch(/^https:\/\/github\.com\//);
      expect(i.zweck.length).toBeGreaterThan(10);
      expect(STUFEN).toContain(i.abStufe);
      // Extern angebundene Dienste brauchen mindestens eine ENV; builtin/lib nicht.
      if (i.immerAktiv) expect(i.envKeys.length).toBe(0);
      else expect(i.envKeys.length).toBeGreaterThan(0);
      // Health-Konfiguration ist paarweise vollständig.
      if (i.healthUrlEnv) expect(i.healthPfad).toBeTruthy();
    }
  });

  it("Stufen-Gating ist monoton (höhere Stufe = mind. so viele Integrationen)", () => {
    const zahlen = STUFEN.map((s) => integrationsFuerStufe(s).length);
    for (let k = 1; k < zahlen.length; k++) {
      expect(zahlen[k]).toBeGreaterThanOrEqual(zahlen[k - 1]);
    }
    // ENTERPRISE enthält alle.
    expect(integrationsFuerStufe("ENTERPRISE").length).toBe(INTEGRATIONS.length);
  });

  it("integrationById findet reale Einträge und nichts Erfundenes", () => {
    expect(integrationById("ollama")?.kind).toBe("local-llm");
    expect(integrationById("gibt-es-nicht")).toBeUndefined();
  });

  it("erweiterter Katalog: neue Module vorhanden und richtig kategorisiert", () => {
    // Datei-Extraktion (ergänzt den Datei-Anhang) und STT (für Aufnahmen).
    expect(integrationById("tika")?.kind).toBe("extract");
    expect(integrationById("whisper")?.kind).toBe("stt");
    // Geräte-/Anlagensteuerung – die ehrliche Antwort auf „ganze Maschine/Abteilung".
    const ha = integrationById("home-assistant");
    expect(ha?.kind).toBe("automation");
    expect(ha?.abStufe).toBe("ENTERPRISE");
    // Sicherheitskritisch → braucht einen Freigabe-Hinweis.
    expect(ha?.hinweis).toMatch(/Freigabe/i);
    expect(integrationById("node-red")?.kind).toBe("automation");
  });

  it("Automations-Module sind self-hosted und nur ab höheren Stufen", () => {
    const automation = INTEGRATIONS.filter((i) => i.kind === "automation");
    expect(automation.length).toBeGreaterThanOrEqual(2);
    for (const i of automation) {
      expect(i.selbstGehostet).toBe(true);
      expect(["BUSINESS", "ENTERPRISE"]).toContain(i.abStufe);
    }
  });
});

describe("Integrations-Status", () => {
  const ollama = integrationById("ollama")!;
  const playwright = integrationById("playwright")!;

  it("immerAktiv gilt als bereit ohne ENV", () => {
    expect(istKonfiguriert(playwright, {})).toBe(true);
    expect(grundStatus(playwright, {})).toBe("bereit");
  });

  it("ohne ENV ehrlich nicht-konfiguriert", () => {
    expect(istKonfiguriert(ollama, {})).toBe(false);
    expect(grundStatus(ollama, {})).toBe("nicht-konfiguriert");
    expect(healthUrl(ollama, {})).toBeNull();
  });

  it("mit ENV konfiguriert und Health-URL korrekt gebaut", () => {
    const env = { LOCAL_LLM_URL: "http://localhost:11434/" };
    expect(istKonfiguriert(ollama, env)).toBe(true);
    expect(grundStatus(ollama, env)).toBe("konfiguriert");
    expect(healthUrl(ollama, env)).toBe("http://localhost:11434/api/tags");
  });

  it("pingIntegration: erreichbar → aktiv, offline → konfiguriert, ohne ENV → nicht-konfiguriert", async () => {
    const env = { LOCAL_LLM_URL: "http://svc:11434" };
    const okFetch = (async () => ({ ok: true })) as unknown as typeof fetch;
    const failFetch = (async () => {
      throw new Error("offline");
    }) as unknown as typeof fetch;

    expect(await pingIntegration(ollama, { env, fetchImpl: okFetch })).toBe("aktiv");
    expect(await pingIntegration(ollama, { env, fetchImpl: failFetch })).toBe("konfiguriert");
    expect(await pingIntegration(ollama, { env: {}, fetchImpl: okFetch })).toBe("nicht-konfiguriert");
  });
});
