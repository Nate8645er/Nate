"use client";

/**
 * Freigabe & Ausgang – zentrale Station: alle Mission-Ergebnisse an einem Ort
 * ansehen, freigeben und kopieren, bevor Sie sie verwenden/versenden. Arbeitet
 * mit den ECHTEN Ergebnissen aus dem Verlauf (localStorage); nichts erfunden.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  eintragId,
  statusVon,
  umschalten,
  filtere,
  zusammenfassung,
  type ErgebnisEintrag,
  type StatusMap,
} from "@/lib/freigabe";

const HISTORY_KEY = "acc-mission-history";
const FREIGABE_KEY = "acc-freigaben";

function ladeHistory(): ErgebnisEintrag[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const arr = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(arr) ? (arr as ErgebnisEintrag[]).filter((e) => e && typeof e.final === "string") : [];
  } catch {
    return [];
  }
}
function ladeStatus(): StatusMap {
  try {
    const raw = localStorage.getItem(FREIGABE_KEY);
    const obj = raw ? (JSON.parse(raw) as unknown) : {};
    return obj && typeof obj === "object" ? (obj as StatusMap) : {};
  } catch {
    return {};
  }
}

function datum(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleString("de-CH", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export default function FreigabeClient() {
  const [eintraege, setEintraege] = useState<ErgebnisEintrag[]>([]);
  const [statusMap, setStatusMap] = useState<StatusMap>({});
  const [filter, setFilter] = useState<"alle" | "offen" | "freigegeben">("offen");
  const [offen, setOffen] = useState<string | null>(null);
  const [kopiert, setKopiert] = useState<string | null>(null);

  useEffect(() => {
    setEintraege(ladeHistory());
    setStatusMap(ladeStatus());
  }, []);

  const speichereStatus = useCallback((next: StatusMap) => {
    setStatusMap(next);
    try { localStorage.setItem(FREIGABE_KEY, JSON.stringify(next)); } catch { /* Speicher voll/gesperrt */ }
  }, []);

  const toggle = useCallback((id: string) => speichereStatus(umschalten(statusMap, id)), [statusMap, speichereStatus]);

  const kopieren = useCallback(async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setKopiert(id);
      window.setTimeout(() => setKopiert((k) => (k === id ? null : k)), 1600);
    } catch { /* Clipboard nicht verfügbar */ }
  }, []);

  const summe = useMemo(() => zusammenfassung(eintraege, statusMap), [eintraege, statusMap]);
  const sichtbar = useMemo(() => filtere(eintraege, statusMap, filter), [eintraege, statusMap, filter]);

  const tab = (id: typeof filter, label: string, n: number) => (
    <button
      type="button"
      onClick={() => setFilter(id)}
      className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
        filter === id
          ? "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] text-white"
          : "border border-[#e0d8c6] bg-white/70 text-[#6f6557] hover:text-[#c25e0e]"
      }`}
    >
      {label} <span className="opacity-70">{n}</span>
    </button>
  );

  return (
    <div className="mx-auto max-w-3xl">
      <div className="acc-in">
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Freigabe &amp; Ausgang</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight sm:text-4xl">
          Alles an <span className="acc-grad-text">einem Ort</span> freigeben
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-[#6f6557]">
          Jedes fertige Ergebnis Ihrer KI-Abteilung landet hier. Prüfen, freigeben und
          kopieren – bevor Sie es versenden oder verwenden.
        </p>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {tab("offen", "Offen", summe.offen)}
        {tab("freigegeben", "Freigegeben", summe.freigegeben)}
        {tab("alle", "Alle", summe.gesamt)}
      </div>

      {sichtbar.length === 0 ? (
        <div className="acc-card mt-6 rounded-2xl p-8 text-center">
          <p className="text-sm text-[#6f6557]">
            {eintraege.length === 0
              ? "Noch keine Ergebnisse. Starten Sie eine Mission im Dashboard – die Ergebnisse erscheinen hier zur Freigabe."
              : "In diesem Filter ist nichts. Wechseln Sie oben den Filter."}
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {sichtbar.map((e) => {
            const id = eintragId(e);
            const frei = statusVon(statusMap, id) === "freigegeben";
            const auf = offen === id;
            return (
              <article key={id} className="acc-card rounded-2xl p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-[#1c1917]" title={e.goal}>{e.goal || "Mission"}</h3>
                    <p className="mt-0.5 text-xs text-[#8a8172]">
                      {datum(e.at)}
                      {typeof e.score === "number" ? ` · Quality-Score ${e.score}` : ""}
                      {e.artifacts?.length ? ` · ${e.artifacts.length} Datei(en)` : ""}
                    </p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                      frei ? "bg-[#e7f6ee] text-[#177245]" : "bg-[#fff4e6] text-[#c25e0e]"
                    }`}
                  >
                    {frei ? "Freigegeben" : "Offen"}
                  </span>
                </div>

                <p className={`mt-3 whitespace-pre-wrap text-sm text-[#4a4335] ${auf ? "" : "line-clamp-3"}`}>
                  {e.final}
                </p>
                {e.final.length > 180 && (
                  <button
                    type="button"
                    onClick={() => setOffen(auf ? null : id)}
                    className="mt-1 text-xs font-semibold text-[#c25e0e] hover:underline"
                  >
                    {auf ? "Weniger anzeigen" : "Ganzes Ergebnis anzeigen"}
                  </button>
                )}

                <div className="mt-4 flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => toggle(id)}
                    className={`rounded-full px-4 py-2 text-sm font-bold transition ${
                      frei
                        ? "border border-[#e0d8c6] bg-white/70 text-[#4a4335] hover:text-[#c25e0e]"
                        : "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] text-white hover:brightness-105"
                    }`}
                  >
                    {frei ? "Freigabe zurücknehmen" : "Freigeben ✓"}
                  </button>
                  <button
                    type="button"
                    onClick={() => kopieren(id, e.final)}
                    className="rounded-full border border-[#e0d8c6] bg-white/70 px-4 py-2 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]"
                  >
                    {kopiert === id ? "Kopiert ✓" : "Ergebnis kopieren"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
