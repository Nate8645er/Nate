/**
 * Ein-Key-Betrieb: Der Betreiber hinterlegt nur EINEN Provider-Key (z. B.
 * ANTHROPIC_API_KEY). resolveProviderModel muss dann jeden Agenten – egal
 * welcher native Provider konfiguriert ist – auf den vorhandenen Provider
 * umleiten, damit das gesamte Team echt arbeitet und der Kunde nie einen
 * eigenen Key braucht. Ohne jeden Key darf es null liefern (Demo-Fallback).
 */

import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  firstConfiguredProvider,
  hasApiKey,
  resolveProviderModel,
} from "@/lib/agents/providers";

/** Alle Provider-Keys, die den Ein-Key-Betrieb beeinflussen. */
const KEY_ENV = [
  "ANTHROPIC_API_KEY",
  "OPENAI_API_KEY",
  "MOONSHOT_API_KEY",
  "GOOGLE_API_KEY",
  "XAI_API_KEY",
  "DEEPSEEK_API_KEY",
  "MISTRAL_API_KEY",
  "QWEN_API_KEY",
  "META_API_KEY",
  "META_LLM_URL",
  "LOCAL_LLM_URL",
] as const;

describe("Ein-Key-Betrieb (resolveProviderModel)", () => {
  const gesichert: Record<string, string | undefined> = {};

  beforeEach(() => {
    for (const k of KEY_ENV) {
      gesichert[k] = process.env[k];
      delete process.env[k];
    }
  });

  afterEach(() => {
    for (const k of KEY_ENV) {
      if (gesichert[k] === undefined) delete process.env[k];
      else process.env[k] = gesichert[k];
    }
  });

  it("leitet Agenten ohne eigenen Key auf den vorhandenen Anthropic-Key um", () => {
    process.env.ANTHROPIC_API_KEY = "sk-ant-test";

    // Builder läuft nativ über openai, Analyst über moonshot – beide nicht gesetzt.
    const builder = resolveProviderModel("openai", "gpt-4o-mini");
    const analyst = resolveProviderModel("moonshot", "kimi-k3");

    expect(builder).toEqual({ provider: "anthropic", model: "claude-sonnet-5" });
    expect(analyst).toEqual({ provider: "anthropic", model: "claude-sonnet-5" });
  });

  it("lässt einen Agenten unverändert, wenn sein nativer Provider einen Key hat", () => {
    process.env.ANTHROPIC_API_KEY = "sk-ant-test";
    process.env.OPENAI_API_KEY = "sk-openai-test";

    // openai ist konfiguriert -> keine Umleitung, Original-Modell bleibt.
    expect(resolveProviderModel("openai", "gpt-4o-mini")).toEqual({
      provider: "openai",
      model: "gpt-4o-mini",
    });
    // moonshot fehlt weiterhin -> Umleitung auf ersten konfigurierten (anthropic).
    expect(resolveProviderModel("moonshot", "kimi-k3")).toEqual({
      provider: "anthropic",
      model: "claude-sonnet-5",
    });
  });

  it("gibt null zurück, wenn gar kein Provider konfiguriert ist", () => {
    expect(firstConfiguredProvider()).toBeNull();
    expect(resolveProviderModel("anthropic", "claude-sonnet-5")).toBeNull();
    expect(hasApiKey("anthropic")).toBe(false);
  });

  it("respektiert eine Modell-Override per <PROVIDER>_MODEL beim Umleiten", () => {
    process.env.ANTHROPIC_API_KEY = "sk-ant-test";
    process.env.ANTHROPIC_MODEL = "claude-opus-4-8";

    const umgeleitet = resolveProviderModel("openai", "gpt-4o-mini");
    expect(umgeleitet).toEqual({ provider: "anthropic", model: "claude-opus-4-8" });

    delete process.env.ANTHROPIC_MODEL;
  });
});
