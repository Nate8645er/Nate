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
import { talentBeispiele, talentpoolFormatiert } from "@/lib/talentpool";
import type { AgentRole, PlanId } from "@/lib/agents/types";

/** Seite wird serverseitig alle 30 Minuten neu erzeugt (ISR) –
 *  damit rotieren auch die Talent-Pool-Beispiele halbstündlich. */
export const revalidate = 1800;
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

export const metadata: Metadata = {
  title: "Ihre Belegschaft | AI Command Center",
  description:
    "Das Team hinter jeder Mission: Commander, Spezialisten und die skalierende KI-Belegschaft pro Abo-Stufe.",
};

const KERN: AgentRole[] = ["commander", "builder", "analyst", "quality"];
const SPEZIALISTEN: AgentRole[] = ["marketing", "coding", "research", "business"];
const PLAN_REIHENFOLGE: PlanId[] = ["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];

const PLAN_NOTIZ: Record<PlanId, string> = {
  FREE: "Kern-Team zum Kennenlernen",
  PERSONAL: "Kern-Team für Einzelpersonen – der günstige Einstieg",
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
          <WorkNav aktiv="team" variante="dunkel" />
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

        {/* Talent-Pool: ueber 1 Milliarde adressierbare Profile */}
        <TalentPool />
        <WorkFooter variante="dunkel" />
      </div>
    </div>
  );
}

/**
 * Generativer Talent-Pool. Die Beispiel-Profile rotieren mit jeder
 * ISR-Regeneration (alle 30 Minuten) – der Seed ist das aktuelle
 * 30-Minuten-Fenster zum Zeitpunkt der Server-Erzeugung.
 */
function TalentPool() {
  const seed = Math.floor(Date.now() / 1_800_000);
  const beispiele = talentBeispiele(6, seed);
  const stand = new Date().toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" });
  return (
    <section className="mt-12">
      <h2 className="text-xl font-semibold text-white">Der Talent-Pool dahinter</h2>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
        Ihr Commander besetzt jede Mission aus einem generativen Pool von{" "}
        <span className="font-semibold text-[#ffd257]">{talentpoolFormatiert()}</span>{" "}
        adressierbaren Spezialisten-Profilen (Rolle × Fachgebiet × Branche ×
        Spezialisierung × Markt × Stufe). Jedes Profil ist über seine Nummer
        abrufbar und wird bei Bedarf instanziiert – rund um die Uhr, an jedem
        Tag. Sechs Beispiele aus dem Pool (Auswahl rotiert alle 30 Minuten,
        Stand {stand} Uhr):
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {beispiele.map((p) => (
          <div key={p.index} className="hud-panel rounded-xl p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#ffb35c]/60">
              Profil #{p.index.toLocaleString("de-CH")}
            </p>
            <p className="mt-1.5 text-sm font-semibold text-[#ffb35c]">{p.titel}</p>
            <p className="mt-1 text-xs leading-relaxed text-zinc-500">
              {p.branche} · {p.spezialisierung} · Markt {p.markt}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 max-w-2xl text-xs leading-relaxed text-zinc-500">
        Ehrlich erklärt: Der Pool ist der Adressraum, aus dem live besetzt
        wird – nicht eine Milliarde gleichzeitig laufender Rechenprozesse.
        Wie viele Spezialisten pro Auftrag gleichzeitig rechnen, bestimmt
        Ihre Abo-Stufe (Tabelle oben). Genau diese Kombination macht das
        System gross UND schnell.
      </p>
    </section>
  );
}
