/**
 * Team – Ihre Belegschaft im Überblick.
 *
 * Server-gerendert aus der echten Team-Konfiguration (lib/agents/team.ts):
 * Kern-Team, Spezialisten und wie die Belegschaft pro Abo-Stufe wächst.
 * Es werden bewusst nur Name/Beschreibung angezeigt – System-Prompts
 * bleiben serverseitig.
 */

import type { Metadata } from "next";
import Link from "next/link";
import { AGENTS, WORKERS_BY_PLAN, WORKFORCE_BY_PLAN, MAX_DYN_AGENTS } from "@/lib/agents/team";
import type { AgentRole, PlanId } from "@/lib/agents/types";

export const metadata: Metadata = {
  title: "Ihre Belegschaft | AI Command Center",
  description:
    "Das Team hinter jeder Mission: Commander, Spezialisten und die skalierende KI-Belegschaft pro Abo-Stufe.",
};

const KERN: AgentRole[] = ["commander", "builder", "analyst", "quality"];
const SPEZIALISTEN: AgentRole[] = ["marketing", "coding", "research", "business"];
const PLAN_REIHENFOLGE: PlanId[] = ["FREE", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];

const PLAN_NOTIZ: Record<PlanId, string> = {
  FREE: "Kern-Team zum Kennenlernen",
  STARTER: "Kern-Team, jeden Tag einsatzbereit",
  PROFESSIONAL: "Kern-Team + alle 4 Spezialisten parallel",
  BUSINESS: `Virtuelle Firma: dynamische Abteilungen, bis ${MAX_DYN_AGENTS.BUSINESS} Spezialisten live pro Auftrag`,
  ENTERPRISE: `Maximalausbau: bis ${MAX_DYN_AGENTS.ENTERPRISE} Spezialisten live pro Auftrag, Belegschaft 1000`,
};

export default function TeamPage() {
  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <Link href="/chat" className="hover:text-[#ffb35c]">Kommando</Link>
            <Link href="/workflows" className="hidden hover:text-[#ffb35c] sm:inline">Autopilot</Link>
            <Link href="/berichte" className="hidden hover:text-[#ffb35c] sm:inline">Berichte</Link>
            <span className="text-[#ffb35c]">Team</span>
          </nav>
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">Ihre Belegschaft</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            Das Team hinter jedem Befehl
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Kein einzelner Chatbot, sondern eine Organisation: Der Commander
            plant und delegiert, Spezialisten führen aus, Quality prüft jedes
            Ergebnis, bevor Sie es sehen. Je höher die Stufe, desto grösser die
            Firma, die für Sie arbeitet.
          </p>
        </div>

        {/* Kern-Team */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-white">Kern-Team</h2>
          <p className="mt-1 text-sm text-zinc-500">In jeder Stufe dabei – von FREE bis ENTERPRISE.</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {KERN.map((r) => (
              <article key={r} className="hud-panel rounded-xl p-5">
                <h3 className="font-semibold text-[#ffb35c]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Spezialisten */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-white">Spezialisten</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Ab PROFESSIONAL arbeiten alle vier parallel mit – jeder mit eigenem Fachgebiet und eigenem KI-Modell.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {SPEZIALISTEN.map((r) => (
              <article key={r} className="hud-panel rounded-xl p-5">
                <h3 className="font-semibold text-[#ffb35c]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Skalierung pro Plan */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-white">So wächst Ihre Firma</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-[#ff8c2a]/25 text-left">
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#ffb35c]">Stufe</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#ffb35c]">Aktive Worker</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#ffb35c]">Belegschaft</th>
                  <th className="py-3 font-mono text-[11px] uppercase tracking-[0.16em] text-[#ffb35c]">Was das bedeutet</th>
                </tr>
              </thead>
              <tbody>
                {PLAN_REIHENFOLGE.map((p) => (
                  <tr key={p} className="border-b border-[#ff8c2a]/10">
                    <td className="py-3 pr-4 font-semibold text-white">{p}</td>
                    <td className="py-3 pr-4 text-zinc-300">
                      {WORKERS_BY_PLAN[p].length} + Commander + Quality
                    </td>
                    <td className="py-3 pr-4 text-[#ffd257]">{WORKFORCE_BY_PLAN[p]}</td>
                    <td className="py-3 text-zinc-400">{PLAN_NOTIZ[p]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-2xl text-xs leading-relaxed text-zinc-500">
            Transparenz: «Belegschaft» ist die sichtbare virtuelle Organisation
            Ihrer Firma (Abteilungen, Rollen, Assistenzen). Die Zahl der
            gleichzeitig live rechnenden KI-Spezialisten ist pro Stufe begrenzt
            – das hält jede Mission schnell, stabil und bezahlbar.
          </p>
          <div className="mt-6">
            <Link
              href="/chat"
              className="shop-btn inline-block rounded-lg bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-[#1a0f04]"
            >
              Befehl an die Belegschaft geben
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
