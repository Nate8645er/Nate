/**
 * Freigabe & Ausgang: reine, testbare Logik für die Inbox. Arbeitet mit den
 * ECHTEN Mission-Ergebnissen aus der Verlaufsliste (localStorage acc-mission-
 * history) – nichts wird erfunden. Der Freigabe-Status wird separat gehalten
 * (localStorage acc-freigaben), damit der Verlauf unverändert bleibt.
 */

export type FreigabeStatus = "offen" | "freigegeben";

/** Ergebnis-Eintrag, wie ihn das Dashboard speichert (Teilmenge). */
export interface ErgebnisEintrag {
  goal: string;
  final: string;
  score: number | null;
  at: string;
  artifacts?: { path: string; content: string; language: string }[];
}

export type StatusMap = Record<string, FreigabeStatus>;

/** Stabile Kennung eines Eintrags (Zeitstempel; Fallback: Ziel+Index-frei). */
export function eintragId(e: ErgebnisEintrag): string {
  return (e.at && String(e.at)) || `goal:${e.goal.slice(0, 40)}`;
}

/** Status eines Eintrags (Standard: "offen"). */
export function statusVon(map: StatusMap, id: string): FreigabeStatus {
  return map[id] === "freigegeben" ? "freigegeben" : "offen";
}

/** Status umschalten (offen ↔ freigegeben) und die NEUE Map zurückgeben. */
export function umschalten(map: StatusMap, id: string): StatusMap {
  const neu: StatusMap = { ...map };
  neu[id] = statusVon(map, id) === "freigegeben" ? "offen" : "freigegeben";
  return neu;
}

/** Setzt einen expliziten Status und gibt die neue Map zurück. */
export function setzeStatus(map: StatusMap, id: string, status: FreigabeStatus): StatusMap {
  return { ...map, [id]: status };
}

/**
 * Filtert die Einträge nach Status. "alle" = alle. Reihenfolge bleibt erhalten
 * (das Dashboard speichert neueste zuerst).
 */
export function filtere(
  eintraege: readonly ErgebnisEintrag[],
  map: StatusMap,
  filter: "alle" | FreigabeStatus,
): ErgebnisEintrag[] {
  if (filter === "alle") return [...eintraege];
  return eintraege.filter((e) => statusVon(map, eintragId(e)) === filter);
}

/** Kennzahlen für die Kopfzeile. */
export function zusammenfassung(
  eintraege: readonly ErgebnisEintrag[],
  map: StatusMap,
): { gesamt: number; offen: number; freigegeben: number } {
  let offen = 0;
  let freigegeben = 0;
  for (const e of eintraege) {
    if (statusVon(map, eintragId(e)) === "freigegeben") freigegeben++;
    else offen++;
  }
  return { gesamt: eintraege.length, offen, freigegeben };
}
