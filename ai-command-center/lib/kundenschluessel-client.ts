/**
 * Client-seitige Verwaltung des eigenen LLM-Schlüssels des Kunden
 * („Bring your own key"). Der Schlüssel liegt AUSSCHLIESSLICH im Browser des
 * Kunden (localStorage) und wird pro Mission als Header mitgeschickt — er wird
 * nie an einen Server des Betreibers gespeichert. So verbindet der Kunde sein
 * Unternehmen mit seinem eigenen KI-Zugang und trägt seine Nutzungskosten selbst.
 */

export const LLM_PROVIDER_KEY = "acc-llm-provider";
export const LLM_KEY_KEY = "acc-llm-key";

export interface GespeicherterSchluessel {
  provider: string;
  key: string;
}

export function kundenSchluesselLaden(): GespeicherterSchluessel | null {
  try {
    const provider = localStorage.getItem(LLM_PROVIDER_KEY);
    const key = localStorage.getItem(LLM_KEY_KEY);
    if (provider && key) return { provider, key };
  } catch {
    /* Storage nicht verfügbar */
  }
  return null;
}

export function kundenSchluesselSpeichern(provider: string, key: string): void {
  try {
    localStorage.setItem(LLM_PROVIDER_KEY, provider);
    localStorage.setItem(LLM_KEY_KEY, key.trim());
  } catch {
    /* Storage nicht schreibbar */
  }
}

export function kundenSchluesselLoeschen(): void {
  try {
    localStorage.removeItem(LLM_PROVIDER_KEY);
    localStorage.removeItem(LLM_KEY_KEY);
  } catch {
    /* egal */
  }
}

/** Header (Provider + Key) für den Mission-Request. Leer, wenn nichts gesetzt. */
export function kundenSchluesselHeaders(): Record<string, string> {
  const s = kundenSchluesselLaden();
  return s ? { "x-acc-llm-provider": s.provider, "x-acc-llm-key": s.key } : {};
}
