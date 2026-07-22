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
import { ratStatus } from "@/lib/agents/council";
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
  PROFESSIONAL: "Kern-Team + Marketing & Research parallel",
  BUSINESS: `Virtuelle Firma: dynamische Abteilungen, bis ${MAX_DYN_AGENTS.BUSINESS} Spezialisten live pro Auftrag`,
  ENTERPRISE: `Maximalausbau: bis ${MAX_DYN_AGENTS.ENTERPRISE} Spezialisten live pro Auftrag, Belegschaft 1000`,
};

export default function TeamPage() {
  const rat = ratStatus();
  const ratBoss = rat.find((m) => m.boss);
  const ratWorker = rat.filter((m) => !m.boss);
  const ratAktiv = rat.filter((m) => m.aktiv).length;
  return (
    <div className="acc-page min-h-dvh text-[#2a2521]">
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#1c1917]/10 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#c25e0e]/85">AI Command Center</span>
          </div>
          <WorkNav aktiv="team" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="mb-3 font-mono text-[11px] uppercase tracking-[0.22em] text-[#c25e0e]/85">Ihre Belegschaft</p>
          <h1 className="text-3xl font-semibold text-[#1c1917] sm:text-4xl">
            Das Team hinter jedem Befehl
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#5c5346]">
            Kein einzelner Chatbot, sondern eine Organisation: Der Commander
            plant und delegiert, Spezialisten führen aus, Quality prüft jedes
            Ergebnis, bevor Sie es sehen. Je höher die Stufe, desto grösser die
            Firma, die für Sie arbeitet.
          </p>
        </div>

        {/* Modell-Rat: mehrere Frontier-Modelle als Worker unter dem Boss */}
        <section className="mt-10">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-xl font-semibold text-[#1c1917]">Modell-Rat</h2>
            <span className="text-xs text-[#8d8172]">{ratAktiv} von {rat.length} Modellen einsatzbereit</span>
          </div>
          <p className="mt-1 max-w-2xl text-sm text-[#8d8172]">
            Nicht ein Modell, sondern ein Team führender KI-Modelle. Der Boss
            verteilt jeden Auftrag an die Worker und führt ihre Antworten
            zusammen. Jedes Modell wird aktiv, sobald sein Zugang hinterlegt ist.
          </p>

          {ratBoss && (
            <article className="acc-card mt-4 rounded-xl border-l-2 border-[#ff8c2a] p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-[#ff8c2a]">Boss · Orchestrator</span>
                  <h3 className="mt-0.5 font-semibold text-[#c25e0e]">
                    {ratBoss.label} <span className="text-xs font-normal text-[#8d8172]">· {ratBoss.hersteller}</span>
                  </h3>
                </div>
                <StatusBadge aktiv={ratBoss.aktiv} />
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#5c5346]">{ratBoss.rolle}</p>
            </article>
          )}

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {ratWorker.map((m) => (
              <article key={m.id} className="acc-card rounded-xl p-5">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-[#c25e0e]">
                    {m.label} <span className="text-xs font-normal text-[#8d8172]">· {m.hersteller}</span>
                  </h3>
                  <StatusBadge aktiv={m.aktiv} />
                </div>
                <p className="mt-2 text-sm leading-relaxed text-[#5c5346]">{m.rolle}</p>
              </article>
            ))}
          </div>
          <p className="mt-3 text-xs text-[#a89e8d]">
            Zugänge werden serverseitig als Umgebungsvariablen hinterlegt
            (siehe .env.example). Ohne Zugang bleibt ein Modell sichtbar, aber
            inaktiv – wir versprechen nichts, was nicht real läuft.
          </p>
        </section>

        {/* Kern-Team */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-[#1c1917]">Kern-Team</h2>
          <p className="mt-1 text-sm text-[#8d8172]">In jeder Stufe dabei – von FREE bis ENTERPRISE.</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {KERN.map((r) => (
              <article key={r} className="acc-card rounded-xl p-5">
                <h3 className="font-semibold text-[#c25e0e]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#5c5346]">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Spezialisten */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-[#1c1917]">Spezialisten</h2>
          <p className="mt-1 text-sm text-[#8d8172]">
            Ab PROFESSIONAL kommen Marketing &amp; Research parallel dazu; Coding &amp; Business schalten ab BUSINESS frei. Jeder mit eigenem Fachgebiet und eigenem KI-Modell.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {SPEZIALISTEN.map((r) => (
              <article key={r} className="acc-card rounded-xl p-5">
                <h3 className="font-semibold text-[#c25e0e]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#5c5346]">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Skalierung pro Plan */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold text-[#1c1917]">So wächst Ihre Firma</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-[#ff8c2a]/35 text-left">
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Stufe</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Aktive Worker</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Belegschaft</th>
                  <th className="py-3 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Was das bedeutet</th>
                </tr>
              </thead>
              <tbody>
                {PLAN_REIHENFOLGE.map((p) => (
                  <tr key={p} className="border-b border-[#1c1917]/8">
                    <td className="py-3 pr-4 font-semibold text-[#1c1917]">{p}</td>
                    <td className="py-3 pr-4 text-[#4a4335]">
                      {WORKERS_BY_PLAN[p].length} + Commander + Quality
                    </td>
                    <td className="py-3 pr-4 text-[#b45309]">{WORKFORCE_BY_PLAN[p]}</td>
                    <td className="py-3 text-[#5c5346]">{PLAN_NOTIZ[p]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-2xl text-xs leading-relaxed text-[#8d8172]">
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
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}

/** Kleiner Statuspunkt: einsatzbereit (grün) oder Zugang nötig (grau). */
function StatusBadge({ aktiv }: { aktiv: boolean }) {
  return aktiv ? (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400" /> aktiv
    </span>
  ) : (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-[#1c1917]/[0.05] px-2 py-0.5 text-[10px] font-medium text-[#8d8172]">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-zinc-600" /> Zugang nötig
    </span>
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
      <h2 className="text-xl font-semibold text-[#1c1917]">Der Talent-Pool dahinter</h2>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#5c5346]">
        Ihr Commander besetzt jede Mission aus einem generativen Pool von{" "}
        <span className="font-semibold text-[#b45309]">{talentpoolFormatiert()}</span>{" "}
        adressierbaren Spezialisten-Profilen (Rolle × Fachgebiet × Branche ×
        Spezialisierung × Markt × Stufe). Jedes Profil ist über seine Nummer
        abrufbar und wird bei Bedarf instanziiert – rund um die Uhr, an jedem
        Tag. Sechs Beispiele aus dem Pool (Auswahl rotiert alle 30 Minuten,
        Stand {stand} Uhr):
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {beispiele.map((p) => (
          <div key={p.index} className="acc-card rounded-xl p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#c25e0e]/55">
              Profil #{p.index.toLocaleString("de-CH")}
            </p>
            <p className="mt-1.5 text-sm font-semibold text-[#c25e0e]">{p.titel}</p>
            <p className="mt-1 text-xs leading-relaxed text-[#8d8172]">
              {p.branche} · {p.spezialisierung} · Markt {p.markt}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 max-w-2xl text-xs leading-relaxed text-[#8d8172]">
        Ehrlich erklärt: Der Pool ist der Adressraum, aus dem live besetzt
        wird – nicht eine Milliarde gleichzeitig laufender Rechenprozesse.
        Wie viele Spezialisten pro Auftrag gleichzeitig rechnen, bestimmt
        Ihre Abo-Stufe (Tabelle oben). Genau diese Kombination macht das
        System gross UND schnell.
      </p>
    </section>
  );
}
