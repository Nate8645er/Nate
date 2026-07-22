/**
 * Modell-Rat – das Team aus Frontier-Modellen unter einem Chef-Modell.
 *
 * Fable 5 (Anthropic) ist der Boss/Orchestrator: er zerlegt einen Auftrag,
 * verteilt ihn an die konfigurierten Modell-Worker und führt deren Antworten
 * zu einem Gesamtergebnis zusammen. Die Worker sind je ein starkes Modell
 * eines anderen Anbieters.
 *
 * Ehrlich: Ein Modell ist nur dann tatsächlich einsatzbereit, wenn sein
 * API-Key (bzw. bei selbst gehosteten die URL) in der Umgebung gesetzt ist.
 * `ratStatus()` liefert genau diese Einsatzbereitschaft, damit die /team-Seite
 * pro Modell „aktiv" oder „API-Key hinterlegen" anzeigen kann – ohne mehr zu
 * versprechen, als der Code liefert.
 */

import type { Provider } from "./types";
import { hasApiKey, modelId } from "./providers";

export interface RatModell {
  /** Stabile Kennung, z. B. "gemini". */
  id: string;
  /** Anzeigename inkl. Version, z. B. "Gemini 3 Ultra". */
  label: string;
  /** Hersteller, z. B. "Google". */
  hersteller: string;
  provider: Provider;
  /** Standard-Modell-ID (per <PROVIDER>_MODEL überschreibbar). */
  standardModell: string;
  /** Rolle/Stärke im Team – ein Satz. */
  rolle: string;
  /** true = Boss/Orchestrator des Rats. */
  boss?: boolean;
}

/**
 * Der Boss und seine Worker. Reihenfolge = Anzeigereihenfolge.
 * Modell-IDs sind sinnvolle Standards; die exakte ID lässt sich pro Anbieter
 * über <PROVIDER>_MODEL setzen, ohne Code-Änderung.
 */
export const MODELL_RAT: readonly RatModell[] = [
  {
    id: "fable",
    label: "Fable 5",
    hersteller: "Anthropic",
    provider: "anthropic",
    standardModell: "claude-fable-5",
    rolle: "Chef-Orchestrator: zerlegt den Auftrag, verteilt ihn an die Worker und führt ihre Antworten zusammen.",
    boss: true,
  },
  {
    id: "gemini",
    label: "Gemini 3 Ultra",
    hersteller: "Google",
    provider: "google",
    standardModell: "gemini-3-ultra",
    rolle: "Multimodales Langkontext-Reasoning, breites Weltwissen und Faktenlage.",
  },
  {
    id: "grok",
    label: "Grok 5",
    hersteller: "xAI",
    provider: "xai",
    standardModell: "grok-5",
    rolle: "Aktuelles Wissen, direkte Einschätzungen und schnelles Reasoning.",
  },
  {
    id: "kimi",
    label: "Kimi (Moonshot)",
    hersteller: "Moonshot AI",
    provider: "moonshot",
    standardModell: modelIdStandard("moonshot", "kimi-k2"),
    rolle: "Sehr langer Kontext, gründliche Analyse und Recherche-Zusammenfassung.",
  },
  {
    id: "qwen",
    label: "Qwen 3 Max",
    hersteller: "Alibaba",
    provider: "qwen",
    standardModell: "qwen3-max",
    rolle: "Starkes mehrsprachiges Reasoning und solide Code-Fähigkeiten.",
  },
  {
    id: "deepseek",
    label: "DeepSeek R2",
    hersteller: "DeepSeek",
    provider: "deepseek",
    standardModell: "deepseek-reasoner",
    rolle: "Tiefes schrittweises Reasoning und Mathematik/Logik.",
  },
  {
    id: "llama",
    label: "Llama 4 Behemoth",
    hersteller: "Meta",
    provider: "meta",
    standardModell: "llama-4-behemoth",
    rolle: "Offenes Grossmodell, selbst hostbar – Unabhängigkeit vom Cloud-Anbieter.",
  },
  {
    id: "sonnet",
    label: "Claude Sonnet 5",
    hersteller: "Anthropic",
    provider: "anthropic",
    standardModell: "claude-sonnet-5",
    rolle: "Ausgewogenes Reasoning, sauberes Schreiben und verlässliche Struktur.",
  },
  {
    id: "mistral",
    label: "Mistral Magistral",
    hersteller: "Mistral AI",
    provider: "mistral",
    standardModell: "magistral-medium-latest",
    rolle: "Effizientes Reasoning aus Europa, schnell und datenschutzfreundlich hostbar.",
  },
];

/** Standard-Modell-ID (mit Env-Override) – für Einträge, die den Team-Default teilen. */
function modelIdStandard(provider: Provider, fallback: string): string {
  return modelId(provider, fallback);
}

/** Der Boss des Rats (Fable 5). */
export const RAT_BOSS: RatModell = MODELL_RAT.find((m) => m.boss) ?? MODELL_RAT[0];

/** Die Worker (alle ausser dem Boss). */
export const RAT_WORKER: readonly RatModell[] = MODELL_RAT.filter((m) => !m.boss);

/** Ein Modell inkl. Live-Einsatzbereitschaft und effektiver Modell-ID. */
export interface RatModellStatus extends RatModell {
  /** true = API-Key/URL konfiguriert → tatsächlich aufrufbar. */
  aktiv: boolean;
  /** Effektive Modell-ID (nach <PROVIDER>_MODEL-Override). */
  effektivesModell: string;
}

/** Alle Rat-Modelle mit Live-Status (serverseitig – liest process.env). */
export function ratStatus(): RatModellStatus[] {
  return MODELL_RAT.map((m) => ({
    ...m,
    aktiv: hasApiKey(m.provider),
    effektivesModell: modelId(m.provider, m.standardModell),
  }));
}

/** Wie viele Rat-Modelle sind einsatzbereit (Key/URL gesetzt)? */
export function ratAktivAnzahl(): number {
  return ratStatus().filter((m) => m.aktiv).length;
}
