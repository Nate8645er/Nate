"use client";

/**
 * Interaktiver Einrichtungs-Bereich: Tarif-Auswahl (nach Kauf automatisch
 * erkannt via localStorage "acc-plan"), Übersichts- und Tarif-Video sowie eine
 * Schritt-für-Schritt-Checkliste, deren Fortschritt lokal gespeichert wird.
 */

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { PlanId } from "@/lib/agents/types";
import { TUTORIALS, UEBERSICHT_VIDEO, tutorialFuer } from "@/lib/onboarding";

const PLAN_IDS = TUTORIALS.map((t) => t.plan);

function istPlan(v: string | null): v is PlanId {
  return !!v && (PLAN_IDS as string[]).includes(v);
}

/** Kleiner, zugänglicher Tooltip (Hover + Fokus, Tastatur-bedienbar). */
function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative ml-1.5 inline-flex align-middle">
      <button
        type="button"
        aria-label={`Hinweis: ${text}`}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-[#e0d8c6] bg-white text-[10px] font-bold text-[#6f6557] hover:border-[#ffb066] hover:text-[#c25e0e] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#ffb066]"
      >
        ?
      </button>
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-xl border border-[#e8e1d2] bg-white p-2.5 text-left text-xs leading-relaxed text-[#4a4335] opacity-0 shadow-[0_16px_40px_-16px_rgba(28,25,23,0.35)] transition-opacity duration-150 group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {text}
      </span>
    </span>
  );
}

export default function OnboardingClient() {
  const [plan, setPlan] = useState<PlanId>("STARTER");
  const [erledigt, setErledigt] = useState<Set<string>>(new Set());
  const [geladen, setGeladen] = useState(false);

  // Tarif nach dem Kauf automatisch erkennen.
  useEffect(() => {
    try {
      const p = localStorage.getItem("acc-plan");
      if (istPlan(p)) setPlan(p);
    } catch {
      /* localStorage nicht verfügbar – Standard bleibt STARTER */
    }
    setGeladen(true);
  }, []);

  // Fortschritt je Tarif laden.
  useEffect(() => {
    if (!geladen) return;
    try {
      const raw = localStorage.getItem(`acc-onboarding-${plan}`);
      const arr = raw ? (JSON.parse(raw) as unknown) : [];
      setErledigt(new Set(Array.isArray(arr) ? (arr as string[]) : []));
    } catch {
      setErledigt(new Set());
    }
  }, [plan, geladen]);

  const tut = useMemo(() => tutorialFuer(plan), [plan]);
  const anzahl = tut.schritte.length;
  const fertig = tut.schritte.filter((s) => erledigt.has(s.id)).length;
  const prozent = anzahl ? Math.round((fertig / anzahl) * 100) : 0;

  function toggle(id: string) {
    setErledigt((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      try {
        localStorage.setItem(`acc-onboarding-${plan}`, JSON.stringify([...next]));
      } catch {
        /* Speichern fehlgeschlagen – Fortschritt bleibt für die Sitzung erhalten */
      }
      return next;
    });
  }

  return (
    <div className="mt-8">
      {/* Übersichtsvideo (real) */}
      <section className="acc-card acc-in overflow-hidden rounded-2xl p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-lg font-semibold">{UEBERSICHT_VIDEO.titel}</h2>
          <span className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-2.5 py-0.5 text-[11px] font-semibold text-[#c25e0e]">
            Überblick · {UEBERSICHT_VIDEO.dauer}
          </span>
        </div>
        <div className="mt-4">
          <video
            controls
            preload="metadata"
            poster={UEBERSICHT_VIDEO.poster}
            className="w-full rounded-xl border border-[#e8e1d2] shadow-[0_18px_50px_-24px_rgba(255,120,40,0.28)]"
          >
            <source src={UEBERSICHT_VIDEO.src} type={UEBERSICHT_VIDEO.src.endsWith(".webm") ? "video/webm" : "video/mp4"} />
            Ihr Browser kann dieses Video nicht abspielen.
          </video>
        </div>
      </section>

      {/* Tarif-Auswahl */}
      <div className="mt-8">
        <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Ihr Tarif</p>
        <div className="mt-2 flex flex-wrap gap-2" role="tablist" aria-label="Tarif wählen">
          {TUTORIALS.map((t) => {
            const aktiv = t.plan === plan;
            return (
              <button
                key={t.plan}
                type="button"
                role="tab"
                aria-selected={aktiv}
                onClick={() => setPlan(t.plan)}
                className={
                  aktiv
                    ? "rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-1.5 text-sm font-bold text-white shadow-[0_6px_18px_-6px_rgba(255,110,30,0.55)]"
                    : "rounded-full border border-[#e0d8c6] bg-white/70 px-4 py-1.5 text-sm font-semibold text-[#4a4335] hover:border-[#ffb066] hover:text-[#c25e0e]"
                }
              >
                {t.name}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
        {/* Tarif-Deep-Dive-Video */}
        <section className="acc-card rounded-2xl p-5 sm:p-6">
          <h2 className="text-lg font-semibold">
            Ihr <span className="acc-grad-text">{tut.name}</span>-Tutorial
          </h2>
          <p className="mt-1 text-sm text-[#6f6557]">{tut.kurz}</p>

          {tut.videoSrc ? (
            <video
              controls
              preload="metadata"
              className="mt-4 w-full rounded-xl border border-[#e8e1d2]"
            >
              <source src={tut.videoSrc} type={tut.videoSrc.endsWith(".webm") ? "video/webm" : "video/mp4"} />
              Ihr Browser kann dieses Video nicht abspielen.
            </video>
          ) : (
            <div className="mt-4 flex flex-col items-center justify-center rounded-xl border border-dashed border-[#e0d8c6] bg-[#faf6ee] px-4 py-10 text-center">
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[#fff4e6] text-[#c25e0e]">
                <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                  <path d="m9 8 7 4-7 4V8Z" strokeLinejoin="round" />
                  <circle cx="12" cy="12" r="9.5" />
                </svg>
              </span>
              <p className="mt-3 text-sm font-semibold text-[#4a4335]">
                Ihr persönliches {tut.name}-Video wird gerade produziert.
              </p>
              <p className="mt-1 max-w-sm text-xs text-[#6f6557]">
                Bis dahin führt Sie das Übersichtsvideo oben plus die Checkliste rechts
                sicher durch die Einrichtung. Sobald das Tarif-Video fertig ist,
                erscheint es automatisch hier.
              </p>
            </div>
          )}

          <div className="mt-5">
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">In {tut.name} enthalten</p>
            <ul className="mt-2 space-y-1.5 text-sm text-[#4a4335]">
              {tut.enthalten.map((e) => (
                <li key={e} className="flex gap-2">
                  <svg viewBox="0 0 20 20" className="mt-1 h-4 w-4 shrink-0 text-[#177245]" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                    <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span>{e}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Interaktive Checkliste */}
        <section className="acc-card rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Einrichtungs-Checkliste</h2>
            <span className="text-sm font-semibold text-[#c25e0e]">{fertig}/{anzahl}</span>
          </div>
          {/* Fortschrittsbalken */}
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#efe9dd]" aria-hidden="true">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] transition-[width] duration-500"
              style={{ width: `${prozent}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-[#6f6557]">
            {prozent === 100
              ? "Alles erledigt – Ihr System ist startklar. 🎉"
              : `Ihr Fortschritt: ${prozent}%. Der Stand wird in diesem Browser gespeichert.`}
          </p>

          <ol className="mt-4 space-y-2.5">
            {tut.schritte.map((s, i) => {
              const done = erledigt.has(s.id);
              return (
                <li
                  key={s.id}
                  className={`rounded-xl border p-3 transition-colors ${
                    done ? "border-[#bfe6cf] bg-[#f0faf4]" : "border-[#e8e1d2] bg-white/60"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <button
                      type="button"
                      onClick={() => toggle(s.id)}
                      aria-pressed={done}
                      aria-label={done ? `„${s.titel}" als offen markieren` : `„${s.titel}" als erledigt markieren`}
                      className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-colors ${
                        done
                          ? "border-[#177245] bg-[#177245] text-white"
                          : "border-[#d9cfbd] bg-white text-[#7c7161] hover:border-[#ffb066]"
                      }`}
                    >
                      {done ? (
                        <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                          <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      ) : (
                        i + 1
                      )}
                    </button>
                    <div className="min-w-0 flex-1">
                      <p className={`text-sm font-semibold ${done ? "text-[#177245]" : "text-[#1c1917]"}`}>
                        {s.titel}
                        {s.tooltip && <Tooltip text={s.tooltip} />}
                      </p>
                      <p className="mt-0.5 text-xs leading-relaxed text-[#6f6557]">{s.text}</p>
                      {s.href && (
                        <Link
                          href={s.href}
                          className="mt-1.5 inline-block text-xs font-semibold text-[#c25e0e] hover:underline"
                        >
                          Dorthin →
                        </Link>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
      </div>
    </div>
  );
}
