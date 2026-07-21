"use client";

/**
 * Berichte – das Ergebnis-Archiv des Unternehmens.
 *
 * Sammelt alle abgeschlossenen Missionen (Dashboard-Verlauf,
 * acc-mission-history) und alle ausgeführten Befehle der Kommandozentrale
 * (acc-kommandos) an einem Ort: durchsuchbar, mit Quality-Score,
 * Datei-Downloads und aufklappbarem Bericht.
 */

import { useEffect, useMemo, useState } from "react";
import type { ArtifactFile } from "@/lib/agents/types";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

const HISTORY_KEY = "acc-mission-history";
const KOMMANDOS_KEY = "acc-kommandos";

interface Bericht {
  quelle: "Mission" | "Kommando";
  goal: string;
  final: string;
  score: number | null;
  at: string;
  artifacts: ArtifactFile[];
}

const MIME_BY_LANGUAGE: Record<string, string> = {
  html: "text/html",
  css: "text/css",
  javascript: "text/javascript",
  markdown: "text/markdown",
  json: "application/json",
};

export default function BerichtePage() {
  const [berichte, setBerichte] = useState<Bericht[]>([]);
  const [suche, setSuche] = useState("");

  useEffect(() => {
    const alle: Bericht[] = [];
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          goal?: string;
          final?: string;
          score?: number | null;
          at?: string;
          artifacts?: ArtifactFile[];
        }[];
        if (Array.isArray(parsed)) {
          for (const e of parsed) {
            if (typeof e?.goal === "string" && typeof e?.final === "string") {
              alle.push({
                quelle: "Mission",
                goal: e.goal,
                final: e.final,
                score: typeof e.score === "number" ? e.score : null,
                at: typeof e.at === "string" ? e.at : "",
                artifacts: Array.isArray(e.artifacts) ? e.artifacts : [],
              });
            }
          }
        }
      }
    } catch {
      /* Verlauf nicht lesbar */
    }
    try {
      const raw = localStorage.getItem(KOMMANDOS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          befehl?: string;
          final?: string | null;
          score?: number | null;
          at?: string;
          artifacts?: ArtifactFile[];
        }[];
        if (Array.isArray(parsed)) {
          for (const e of parsed) {
            if (typeof e?.befehl === "string" && typeof e?.final === "string") {
              alle.push({
                quelle: "Kommando",
                goal: e.befehl,
                final: e.final,
                score: typeof e.score === "number" ? e.score : null,
                at: typeof e.at === "string" ? e.at : "",
                artifacts: Array.isArray(e.artifacts) ? e.artifacts : [],
              });
            }
          }
        }
      }
    } catch {
      /* Kommandos nicht lesbar */
    }
    alle.sort((a, b) => (b.at || "").localeCompare(a.at || ""));
    setBerichte(alle);
  }, []);

  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    if (!q) return berichte;
    return berichte.filter(
      (b) => b.goal.toLowerCase().includes(q) || b.final.toLowerCase().includes(q),
    );
  }, [berichte, suche]);

  const dateienGesamt = berichte.reduce((n, b) => n + b.artifacts.length, 0);

  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <WorkNav aktiv="berichte" variante="dunkel" />
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">Ergebnis-Archiv</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">Berichte und Ergebnisse</h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Alles, was Ihre Belegschaft geliefert hat, an einem Ort:{" "}
            {berichte.length} Ergebnis{berichte.length === 1 ? "" : "se"}, {dateienGesamt}{" "}
            erzeugte Datei{dateienGesamt === 1 ? "" : "en"}. Gespeichert in diesem Browser.
          </p>
          <input
            value={suche}
            onChange={(e) => setSuche(e.target.value)}
            placeholder="Berichte durchsuchen …"
            className="mt-6 w-full max-w-md rounded-lg border border-[#ff8c2a]/25 bg-[#12100d] px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-[#ff8c2a]/60 focus:outline-none"
            aria-label="Berichte durchsuchen"
          />
        </div>

        <div className="mt-8 space-y-4">
          {gefiltert.length === 0 && (
            <p className="rounded-xl border border-[#ff8c2a]/15 px-5 py-8 text-center text-sm text-zinc-500">
              {berichte.length === 0
                ? "Noch keine Ergebnisse. Starten Sie eine Mission im Dashboard oder geben Sie einen Befehl in der Kommandozentrale."
                : "Keine Treffer für diese Suche."}
            </p>
          )}
          {gefiltert.map((b, i) => (
            <article key={i} className="hud-panel relative rounded-xl p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-[#ff8c2a]/30 px-2 py-0.5 text-[11px] text-[#ffb35c]">
                      {b.quelle}
                    </span>
                    {b.at && (
                      <span className="text-xs text-zinc-500">
                        {new Date(b.at).toLocaleString("de-CH")}
                      </span>
                    )}
                    {typeof b.score === "number" && (
                      <span className="rounded-full border border-[#ffd257]/50 bg-[#ffd257]/10 px-2 py-0.5 text-[11px] font-semibold text-[#ffd257]">
                        Score {b.score}
                      </span>
                    )}
                  </div>
                  <h2 className="mt-2 font-semibold text-white">{b.goal}</h2>
                </div>
              </div>

              {b.artifacts.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {b.artifacts.map((f) => (
                    <button
                      key={f.path}
                      onClick={() => download(f)}
                      className="shop-btn rounded-md border border-[#ff8c2a]/30 bg-[#ff8c2a]/[0.05] px-3 py-1.5 font-mono text-xs text-[#ffb35c] hover:border-[#ff8c2a]/60"
                    >
                      📄 {f.path} herunterladen
                    </button>
                  ))}
                </div>
              )}

              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-zinc-400 hover:text-[#ffb35c]">
                  Bericht anzeigen
                </summary>
                <div className="mt-3 whitespace-pre-wrap border-t border-[#ff8c2a]/15 pt-3 text-sm leading-relaxed text-zinc-300">
                  {b.final}
                </div>
              </details>
            </article>
          ))}
        </div>
        <WorkFooter variante="dunkel" />
      </div>
    </div>
  );
}

function download(f: ArtifactFile) {
  const blob = new Blob([f.content], {
    type: `${MIME_BY_LANGUAGE[f.language] ?? "text/plain"};charset=utf-8`,
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = f.path.split("/").pop() ?? "datei.txt";
  a.click();
  URL.revokeObjectURL(url);
}
