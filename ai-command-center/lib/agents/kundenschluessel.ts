/**
 * „Bring your own key" — der Kunde verbindet sein Unternehmen mit seinem EIGENEN
 * LLM-Schlüssel. Diese Datei ist reine, testbare Logik: sie liest Provider + Key
 * aus den Request-Headern und validiert sie. Der Schlüssel wird ausschliesslich
 * für die Dauer der Anfrage verwendet (siehe customerKeyStore in providers.ts) —
 * NIE server-seitig gespeichert, NIE geloggt.
 *
 * Transport (vom Browser, nur über HTTPS):
 *   x-acc-llm-provider: anthropic | openai | google | …
 *   x-acc-llm-key:      <der geheime Schlüssel des Kunden>
 */

import type { Provider } from "./types";

/** Alle vom System unterstützten Provider (Cloud + selbst gehostet). */
export const PROVIDER_LISTE: readonly Provider[] = [
  "anthropic", "openai", "moonshot", "local",
  "google", "xai", "qwen", "deepseek", "meta", "mistral",
] as const;

/** Menschliche Namen für die Auswahl im Onboarding. */
export const PROVIDER_LABEL: Record<Provider, string> = {
  anthropic: "Anthropic (Claude)",
  openai: "OpenAI (GPT)",
  google: "Google (Gemini)",
  xai: "xAI (Grok)",
  qwen: "Alibaba (Qwen)",
  deepseek: "DeepSeek",
  mistral: "Mistral",
  moonshot: "Moonshot (Kimi)",
  meta: "Meta (Llama)",
  local: "Eigenes/lokales Modell",
};

export function istProvider(v: unknown): v is Provider {
  return typeof v === "string" && (PROVIDER_LISTE as readonly string[]).includes(v);
}

/**
 * Plausibilitäts-Prüfung eines Schlüssels: nicht leer, keine Leerzeichen/Zeilen-
 * umbrüche, sinnvolle Länge. Bewusst KEINE providerspezifische Präfix-Prüfung
 * (Formate ändern sich); wir verlassen uns auf die echte API-Antwort.
 */
export function schluesselPlausibel(key: unknown): key is string {
  if (typeof key !== "string") return false;
  const k = key.trim();
  return k.length >= 12 && k.length <= 400 && !/\s/.test(k);
}

export interface KundenSchluessel {
  provider: Provider;
  key: string;
}

/**
 * Liest den Kundenschlüssel aus den Headern. Gibt `null` zurück, wenn nichts
 * (oder etwas Ungültiges) mitgeschickt wurde — dann greift der normale Fallback
 * (Betreiber-Env-Key oder ehrlich „nicht konfiguriert").
 */
export function kundenSchluesselAusHeaders(
  get: (name: string) => string | null,
): KundenSchluessel | null {
  const provider = get("x-acc-llm-provider");
  const key = get("x-acc-llm-key");
  if (!istProvider(provider)) return null;
  if (!schluesselPlausibel(key)) return null;
  return { provider, key: (key as string).trim() };
}

/** Baut die Store-Map (Provider → Key) für customerKeyStore.run(). */
export function alsMap(schluessel: KundenSchluessel | null): Record<string, string> {
  return schluessel ? { [schluessel.provider]: schluessel.key } : {};
}
