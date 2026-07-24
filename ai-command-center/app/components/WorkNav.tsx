"use client";

/**
 * WorkNav – plan-bewusste Bereichs-Navigation (2026).
 *
 * Schwebende Glas-Pill-Leiste: Hauptbereiche sichtbar, der Rest im «Mehr»-Menü
 * (nach Themen gruppiert, damit man alles schnell findet). Die Navigation
 * liest den aktiven Plan aus localStorage (`acc-plan`) und zeigt gesperrte
 * Bereiche ehrlich als «ab Plan X» statt sie zu verstecken – so sieht der Kunde
 * den Nutzen des nächsten Abos, ohne im Regen zu stehen.
 */

import Link from "next/link";
import { useEffect, useState } from "react";
import { BEREICH_MIN_PLAN, PLAN_LABEL, PLAN_RANG } from "@/lib/features";
import type { PlanId } from "@/lib/agents/types";

export type BereichId =
  | "missionen"
  | "onboarding"
  | "assistent"
  | "kommando"
  | "kunden"
  | "email"
  | "freigabe"
  | "skills"
  | "werkzeuge"
  | "autopilot"
  | "berichte"
  | "analysen"
  | "agenten"
  | "studio"
  | "team"
  | "benutzer"
  | "einstellungen"
  | "integrationen"
  | "erweiterungen"
  | "status"
  | "sicherheit";

type Eintrag = { id: BereichId; label: string; href: string };

/** Direkt sichtbare Hauptbereiche (Arbeits-Alltag). */
const PRIMAER: Eintrag[] = [
  { id: "missionen", label: "Missionen", href: "/dashboard" },
  { id: "assistent", label: "KI-Chat", href: "/assistent" },
  { id: "kommando", label: "Kommando", href: "/chat" },
  { id: "kunden", label: "Kunden", href: "/kunden" },
  { id: "email", label: "E-Mail", href: "/email" },
  { id: "skills", label: "Skills", href: "/faehigkeiten" },
  { id: "autopilot", label: "Autopilot", href: "/workflows" },
];

/** «Mehr»-Menü, nach Themen sortiert (leichter zu finden). */
const GRUPPEN: { titel: string; eintraege: Eintrag[] }[] = [
  {
    titel: "Arbeiten",
    eintraege: [
      { id: "freigabe", label: "Freigabe & Ausgang", href: "/freigabe" },
      { id: "werkzeuge", label: "Blitz-Werkzeuge", href: "/werkzeuge" },
      { id: "studio", label: "KI-Studio", href: "/studio" },
    ],
  },
  {
    titel: "Team & Automatisierung",
    eintraege: [
      { id: "agenten", label: "Agenten-Übersicht", href: "/agenten" },
      { id: "team", label: "Team", href: "/team" },
      { id: "benutzer", label: "Benutzer", href: "/benutzer" },
    ],
  },
  {
    titel: "Auswertung",
    eintraege: [
      { id: "berichte", label: "Berichte", href: "/berichte" },
      { id: "analysen", label: "Analysen", href: "/analysen" },
    ],
  },
  {
    titel: "Verbindungen",
    eintraege: [
      { id: "integrationen", label: "Integrationen", href: "/integrationen" },
      { id: "erweiterungen", label: "Erweiterungen", href: "/erweiterungen" },
    ],
  },
  {
    titel: "Verwaltung & System",
    eintraege: [
      { id: "onboarding", label: "Einrichtung & Tutorials", href: "/onboarding" },
      { id: "einstellungen", label: "Einstellungen", href: "/einstellungen" },
      { id: "status", label: "System-Status", href: "/status" },
      { id: "sicherheit", label: "Sicherheit", href: "/sicherheit" },
    ],
  },
];

const ALLE_MEHR: Eintrag[] = GRUPPEN.flatMap((g) => g.eintraege);

/** Ist ein Bereich mit dem aktuellen Plan freigeschaltet? */
function freigeschaltet(id: BereichId, plan: PlanId): boolean {
  const min = BEREICH_MIN_PLAN[id];
  return !min || PLAN_RANG[plan] >= PLAN_RANG[min];
}

/** Kurzes «ab Plan X»-Label für gesperrte Bereiche. */
function abLabel(id: BereichId): string | null {
  const min = BEREICH_MIN_PLAN[id];
  return min ? `ab ${PLAN_LABEL[min]}` : null;
}

export default function WorkNav({
  aktiv,
  variante,
}: {
  aktiv: BereichId;
  variante: "hell" | "dunkel";
}) {
  // Plan aus dem Browser lesen (Standard FREE bis geladen).
  const [plan, setPlan] = useState<PlanId>("FREE");
  useEffect(() => {
    try {
      const p = localStorage.getItem("acc-plan") as PlanId | null;
      if (p && p in PLAN_RANG) setPlan(p);
    } catch {
      /* Storage nicht lesbar → FREE */
    }
  }, []);

  const hell = variante === "hell";
  const leiste = hell
    ? "border-[#1c1917]/8 bg-white/60 shadow-[0_2px_16px_-8px_rgba(28,25,23,0.2),inset_0_1px_0_rgba(255,255,255,0.9)]"
    : "border-white/10 bg-white/5 shadow-[0_2px_16px_-8px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.08)]";
  const eintrag = hell
    ? "text-[#6f6557] hover:bg-[#1c1917]/5 hover:text-[#1c1917]"
    : "text-zinc-400 hover:bg-white/8 hover:text-white";
  const aktivPille =
    "bg-gradient-to-r from-[#6366f1] to-[#a855f7] font-semibold text-white shadow-[0_4px_14px_-4px_rgba(99,102,241,0.6)]";
  const menueBg = hell
    ? "border-[#1c1917]/8 bg-white/90 shadow-[0_16px_44px_-16px_rgba(28,25,23,0.28)]"
    : "border-white/10 bg-[#0d0f1c]/95 shadow-[0_16px_44px_-8px_rgba(0,0,0,0.7)]";
  const menueEintrag = hell
    ? "text-[#4a4335] hover:bg-[#6366f1]/10 hover:text-[#4f46e5]"
    : "text-zinc-300 hover:bg-[#6366f1]/15 hover:text-[#a5b4fc]";
  const gruppenTitel = hell ? "text-[#a2988a]" : "text-zinc-500";
  const gesperrt = hell ? "text-[#bdb4a4]" : "text-zinc-600";

  const mehrAktiv = ALLE_MEHR.some((m) => m.id === aktiv);
  const pill = "rounded-full px-3 py-1.5 transition-colors";

  // Nur freigeschaltete Hauptbereiche in der Leiste; gesperrte wandern ins Menü.
  const primaerFrei = PRIMAER.filter((b) => freigeschaltet(b.id, plan));

  return (
    <nav
      className={`flex items-center gap-0.5 rounded-full border p-1 text-[13px] backdrop-blur-xl ${leiste}`}
      aria-label="Bereiche"
    >
      {primaerFrei.map((b, i) =>
        b.id === aktiv ? (
          <span key={b.id} className={`${pill} ${aktivPille}`} aria-current="page">
            {b.label}
          </span>
        ) : (
          <Link
            key={b.id}
            href={b.href}
            className={`${pill} ${eintrag} ${i > 2 ? "hidden lg:inline-block" : i > 1 ? "hidden sm:inline-block" : ""}`}
          >
            {b.label}
          </Link>
        ),
      )}
      <details className="group relative">
        <summary
          className={`flex cursor-pointer list-none items-center gap-1 ${pill} ${mehrAktiv ? aktivPille : eintrag}`}
        >
          Mehr
          <svg viewBox="0 0 12 12" className="h-3 w-3 transition-transform group-open:rotate-180" aria-hidden="true">
            <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </summary>
        <div
          className={`absolute right-0 z-50 mt-3 max-h-[70vh] w-60 overflow-auto rounded-2xl border py-2 backdrop-blur-xl ${menueBg}`}
        >
          {/* Gesperrte Hauptbereiche zuerst als Hinweis (falls vorhanden) */}
          {GRUPPEN.map((g) => {
            const frei = g.eintraege.filter((e) => freigeschaltet(e.id, plan));
            const zu = g.eintraege.filter((e) => !freigeschaltet(e.id, plan));
            if (!frei.length && !zu.length) return null;
            return (
              <div key={g.titel} className="px-1.5 py-1">
                <p className={`px-3 pb-1 pt-1 text-[10px] font-bold uppercase tracking-wider ${gruppenTitel}`}>
                  {g.titel}
                </p>
                {frei.map((b) =>
                  b.id === aktiv ? (
                    <span key={b.id} className="block rounded-lg px-3 py-1.5 font-semibold text-[#6366f1]" aria-current="page">
                      {b.label}
                    </span>
                  ) : (
                    <Link key={b.id} href={b.href} className={`block rounded-lg px-3 py-1.5 ${menueEintrag}`}>
                      {b.label}
                    </Link>
                  ),
                )}
                {zu.map((b) => (
                  <Link
                    key={b.id}
                    href="/preise"
                    className={`flex items-center justify-between gap-2 rounded-lg px-3 py-1.5 ${gesperrt} hover:opacity-80`}
                    title={`Im Abo enthalten ${abLabel(b.id) ?? ""}`}
                  >
                    <span className="flex items-center gap-1.5">
                      <svg viewBox="0 0 16 16" className="h-3 w-3 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true">
                        <rect x="3.5" y="7" width="9" height="6.5" rx="1.2" />
                        <path d="M5.5 7V5.2a2.5 2.5 0 0 1 5 0V7" />
                      </svg>
                      {b.label}
                    </span>
                    <span className="shrink-0 rounded-full bg-gradient-to-r from-[#6366f1] to-[#a855f7] px-2 py-0.5 text-[9px] font-bold text-white">
                      {abLabel(b.id)}
                    </span>
                  </Link>
                ))}
              </div>
            );
          })}
        </div>
      </details>
    </nav>
  );
}
