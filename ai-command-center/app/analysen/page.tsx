"use client";

/**
 * Analysen – Statistikbereich des Unternehmens.
 *
 * Wertet die echten lokalen Arbeitsdaten aus (Missionen im Dashboard,
 * Befehle der Kommandozentrale): Kennzahlen, Aktivität der letzten
 * 14 Tage (SVG-Balken, ohne Fremdbibliothek), Quality-Score-Verlauf.
 * Heller, freundlicher Arbeitsbereich-Stil wie die Kommandozentrale.
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import WorkNav from "@/app/components/WorkNav";
import { usePlanGate } from "@/app/components/PlanGuard";
import WorkFooter from "@/app/components/WorkFooter";

const HISTORY_KEY = "acc-mission-history";
const KOMMANDOS_KEY = "acc-kommandos";

interface Eintrag {
  at: string;
  score: number | null;
  artifacts: number;
}

export default function AnalysenPage() {
  const gate = usePlanGate("analysen", "Analysen");
  const [eintraege, setEintraege] = useState<Eintrag[]>([]);

  useEffect(() => {
    const alle: Eintrag[] = [];
    const lesen = (key: string, atFeld: string, done: (e: Record<string, unknown>) => boolean) => {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) return;
        const parsed = JSON.parse(raw) as Record<string, unknown>[];
        if (!Array.isArray(parsed)) return;
        for (const e of parsed) {
          if (!done(e)) continue;
          alle.push({
            at: typeof e[atFeld] === "string" ? (e[atFeld] as string) : "",
            score: typeof e.score === "number" ? (e.score as number) : null,
            artifacts: Array.isArray(e.artifacts) ? (e.artifacts as unknown[]).length : 0,
          });
        }
      } catch {
        /* Storage nicht lesbar */
      }
    };
    lesen(HISTORY_KEY, "at", (e) => typeof e.final === "string");
    lesen(KOMMANDOS_KEY, "at", (e) => typeof e.final === "string" && e.final !== null);
    alle.sort((a, b) => (a.at || "").localeCompare(b.at || ""));
    setEintraege(alle);
  }, []);

  const scores = eintraege.filter((e) => typeof e.score === "number") as (Eintrag & { score: number })[];
  const avgScore = scores.length
    ? Math.round(scores.reduce((s, e) => s + e.score, 0) / scores.length)
    : null;
  const dateien = eintraege.reduce((s, e) => s + e.artifacts, 0);

  /* Aktivität der letzten 14 Tage */
  const tage: { label: string; count: number }[] = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    tage.push({
      label: d.toLocaleDateString("de-CH", { day: "numeric", month: "numeric" }),
      count: eintraege.filter((e) => e.at.startsWith(key)).length,
    });
  }
  const maxTag = Math.max(1, ...tage.map((t) => t.count));

  const KACHELN = [
    { label: "Erledigte Aufträge", wert: String(eintraege.length) },
    { label: "Erzeugte Dateien", wert: String(dateien) },
    { label: "Ø Quality-Score", wert: avgScore === null ? "–" : String(avgScore) },
    {
      label: "Letzte 7 Tage",
      wert: String(tage.slice(-7).reduce((s, t) => s + t.count, 0)),
    },
  ];

  if (gate) return gate;
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="analysen" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Statistikbereich</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            So arbeitet Ihre KI-Belegschaft
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
            Ausgewertet aus Ihren echten Aufträgen in diesem Browser (Missionen
            und Kommandozentrale). Mandantenweite Auswertungen über alle
            Mitarbeitenden sind Teil der Enterprise-Einrichtung.
          </p>
        </div>

        {/* Kennzahlen */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {KACHELN.map((k) => (
            <div
              key={k.label}
              className="rounded-2xl acc-card p-5"
            >
              <p className="text-3xl font-bold text-[#c25e0e]">{k.wert}</p>
              <p className="mt-1 text-xs font-medium text-[#6f6557]">{k.label}</p>
            </div>
          ))}
        </div>

        {/* Aktivität */}
        <section className="mt-8 rounded-2xl acc-card p-6">
          <h2 className="text-lg font-semibold">Aktivität der letzten 14 Tage</h2>
          <svg viewBox="0 0 560 150" className="mt-4 w-full" role="img" aria-label="Aufträge pro Tag">
            {tage.map((t, i) => {
              const h = Math.round((t.count / maxTag) * 100);
              return (
                <g key={i}>
                  <rect
                    x={i * 40 + 6}
                    y={120 - h}
                    width={28}
                    height={Math.max(2, h)}
                    rx={5}
                    fill={t.count > 0 ? "url(#g)" : "#f0ebe0"}
                  />
                  {t.count > 0 && (
                    <text x={i * 40 + 20} y={112 - h} textAnchor="middle" fontSize="11" fill="#c25e0e" fontWeight="700">
                      {t.count}
                    </text>
                  )}
                  <text x={i * 40 + 20} y={140} textAnchor="middle" fontSize="9" fill="#a2988a">
                    {t.label}
                  </text>
                </g>
              );
            })}
            <defs>
              <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ffb066" />
                <stop offset="100%" stopColor="#ff5f1f" />
              </linearGradient>
            </defs>
          </svg>
        </section>

        {/* Score-Verlauf */}
        <section className="mt-6 rounded-2xl acc-card p-6">
          <h2 className="text-lg font-semibold">Quality-Score-Verlauf</h2>
          {scores.length === 0 ? (
            <p className="mt-3 text-sm text-[#6f6557]">
              Noch keine bewerteten Ergebnisse. Starten Sie einen Befehl in der{" "}
              <Link href="/chat" className="font-medium text-[#c25e0e] hover:underline">Kommandozentrale</Link>.
            </p>
          ) : (
            <div className="mt-4 flex flex-wrap items-end gap-2">
              {scores.slice(-20).map((e, i) => (
                <div key={i} className="flex flex-col items-center gap-1">
                  <span className="text-[10px] font-bold text-[#6f6557]">{e.score}</span>
                  <div
                    className="w-6 rounded-t-md bg-gradient-to-t from-[#ff5f1f] to-[#ffb066]"
                    style={{ height: `${Math.max(6, e.score)}px` }}
                  />
                </div>
              ))}
            </div>
          )}
        </section>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
