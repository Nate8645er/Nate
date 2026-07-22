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
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="berichte" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Ergebnis-Archiv</p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Berichte und <span className="acc-grad-text">Ergebnisse</span>
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
            Alles, was Ihre Belegschaft geliefert hat, an einem Ort:{" "}
            {berichte.length} Ergebnis{berichte.length === 1 ? "" : "se"}, {dateienGesamt}{" "}
            erzeugte Datei{dateienGesamt === 1 ? "" : "en"}. Gespeichert in diesem Browser.
          </p>
          <input
            value={suche}
            onChange={(e) => setSuche(e.target.value)}
            placeholder="Berichte durchsuchen …"
            className="mt-6 w-full max-w-md rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2.5 text-sm placeholder:text-[#7c7161] focus:border-[#ffb066] focus:outline-none"
            aria-label="Berichte durchsuchen"
          />
        </div>

        <div className="mt-8 space-y-4">
          {gefiltert.length === 0 && (
            <p className="rounded-2xl border border-[#e8e1d2] bg-white/60 px-5 py-8 text-center text-sm text-[#6f6557]">
              {berichte.length === 0
                ? "Noch keine Ergebnisse. Starten Sie eine Mission im Dashboard oder geben Sie einen Befehl in der Kommandozentrale."
                : "Keine Treffer für diese Suche."}
            </p>
          )}
          {gefiltert.map((b, i) => (
            <article key={i} className="acc-card acc-card-hover relative rounded-2xl p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${
                        b.quelle === "Mission"
                          ? "bg-[#eef0ff] text-[#5b52d6]"
                          : "bg-[#e6faf6] text-[#0f766e]"
                      }`}
                    >
                      {b.quelle}
                    </span>
                    {b.at && (
                      <span className="text-xs text-[#7c7161]">
                        {new Date(b.at).toLocaleString("de-CH")}
                      </span>
                    )}
                    {typeof b.score === "number" && (
                      <span className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#c25e0e]">
                        Score {b.score}
                      </span>
                    )}
                  </div>
                  <h2 className="mt-2 font-semibold text-[#1c1917]">{b.goal}</h2>
                </div>
              </div>

              {b.artifacts.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {b.artifacts.map((f) => (
                    <button
                      key={f.path}
                      onClick={() => download(f)}
                      className="shop-btn rounded-xl border border-[#e0d8c6] bg-white/70 px-3 py-1.5 font-mono text-xs font-semibold text-[#c25e0e] hover:border-[#ffb066]"
                    >
                      📄 {f.path} herunterladen
                    </button>
                  ))}
                </div>
              )}

              <details className="mt-3">
                <summary className="cursor-pointer text-sm text-[#6f6557] hover:text-[#c25e0e]">
                  Bericht anzeigen
                </summary>
                <div className="mt-3 whitespace-pre-wrap border-t border-[#e8e1d2] pt-3 text-sm leading-relaxed text-[#6f6557]">
                  {b.final}
                </div>
              </details>
            </article>
          ))}
        </div>
        <WorkFooter variante="hell" />
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
