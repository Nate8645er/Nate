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
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="team" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="mb-3 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Ihre Belegschaft</p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Das <span className="acc-grad-text">Team</span> hinter jedem Befehl
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
            Kein einzelner Chatbot, sondern eine Organisation: Der Commander
            plant und delegiert, Spezialisten führen aus, Quality prüft jedes
            Ergebnis, bevor Sie es sehen. Je höher die Stufe, desto grösser die
            Firma, die für Sie arbeitet.
          </p>
        </div>

        {/* Modell-Rat: mehrere Frontier-Modelle als Worker unter dem Boss */}
        <section className="mt-10">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-xl font-semibold">Modell-Rat</h2>
            <span className="text-xs text-[#6f6557]">{ratAktiv} von {rat.length} Modellen einsatzbereit</span>
          </div>
          <p className="mt-1 max-w-2xl text-sm text-[#6f6557]">
            Nicht ein Modell, sondern ein Team führender KI-Modelle. Der Boss
            verteilt jeden Auftrag an die Worker und führt ihre Antworten
            zusammen. Jedes Modell wird aktiv, sobald sein Zugang hinterlegt ist.
          </p>

          {ratBoss && (
            <article className="acc-card acc-card-hover mt-4 rounded-2xl border-l-2 border-[#ff8c2a] p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-[#c25e0e]">Boss · Orchestrator</span>
                  <h3 className="mt-0.5 font-semibold text-[#c25e0e]">
                    {ratBoss.label} <span className="text-xs font-normal text-[#6f6557]">· {ratBoss.hersteller}</span>
                  </h3>
                </div>
                <StatusBadge aktiv={ratBoss.aktiv} />
              </div>
              <p className="mt-2 text-sm leading-relaxed text-[#6f6557]">{ratBoss.rolle}</p>
            </article>
          )}

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {ratWorker.map((m) => (
              <article key={m.id} className="acc-card acc-card-hover rounded-2xl p-5">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="font-semibold text-[#c25e0e]">
                    {m.label} <span className="text-xs font-normal text-[#6f6557]">· {m.hersteller}</span>
                  </h3>
                  <StatusBadge aktiv={m.aktiv} />
                </div>
                <p className="mt-2 text-sm leading-relaxed text-[#6f6557]">{m.rolle}</p>
              </article>
            ))}
          </div>
          <p className="mt-3 text-xs text-[#7c7161]">
            Zugänge werden serverseitig als Umgebungsvariablen hinterlegt
            (siehe .env.example). Ohne Zugang bleibt ein Modell sichtbar, aber
            inaktiv – wir versprechen nichts, was nicht real läuft.
          </p>
        </section>

        {/* Kern-Team – Akzent Indigo */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold">Kern-Team</h2>
          <p className="mt-1 text-sm text-[#6f6557]">In jeder Stufe dabei – von FREE bis ENTERPRISE.</p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {KERN.map((r) => (
              <article key={r} className="acc-card acc-card-hover rounded-2xl border-l-2 border-[#8b5cf6] p-5">
                <h3 className="font-semibold text-[#5b52d6]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#6f6557]">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Spezialisten – Akzent Teal */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold">Spezialisten</h2>
          <p className="mt-1 text-sm text-[#6f6557]">
            Ab PROFESSIONAL kommen Marketing &amp; Research parallel dazu; Coding &amp; Business schalten ab BUSINESS frei. Jeder mit eigenem Fachgebiet und eigenem KI-Modell.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {SPEZIALISTEN.map((r) => (
              <article key={r} className="acc-card acc-card-hover rounded-2xl border-l-2 border-[#2dd4bf] p-5">
                <h3 className="font-semibold text-[#0f766e]">{AGENTS[r].name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#6f6557]">{AGENTS[r].description}</p>
              </article>
            ))}
          </div>
        </section>

        {/* Skalierung pro Plan */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold">So wächst Ihre Firma</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-[#e8e1d2] text-left">
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Stufe</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Aktive Worker</th>
                  <th className="py-3 pr-4 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Belegschaft</th>
                  <th className="py-3 font-mono text-[11px] uppercase tracking-[0.16em] text-[#c25e0e]">Was das bedeutet</th>
                </tr>
              </thead>
              <tbody>
                {PLAN_REIHENFOLGE.map((p) => (
                  <tr key={p} className="border-b border-[#e8e1d2]">
                    <td className="py-3 pr-4 font-semibold text-[#1c1917]">{p}</td>
                    <td className="py-3 pr-4 text-[#6f6557]">
                      {WORKERS_BY_PLAN[p].length} + Commander + Quality
                    </td>
                    <td className="py-3 pr-4 font-semibold text-[#c25e0e]">{WORKFORCE_BY_PLAN[p]}</td>
                    <td className="py-3 text-[#6f6557]">{PLAN_NOTIZ[p]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-2xl text-xs leading-relaxed text-[#6f6557]">
            Transparenz: «Belegschaft» ist die sichtbare virtuelle Organisation
            Ihrer Firma (Abteilungen, Rollen, Assistenzen). Die Zahl der
            gleichzeitig live rechnenden KI-Spezialisten ist pro Stufe begrenzt
            – das hält jede Mission schnell, stabil und bezahlbar.
          </p>
          <div className="mt-6">
            <Link
              href="/chat"
              className="shop-btn inline-block rounded-xl bg-gradient-to-r from-[#ffb066] via-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
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
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-[#e7f6ee] px-2 py-0.5 text-[10px] font-semibold text-[#177245]">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#22c55e]" /> aktiv
    </span>
  ) : (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-[#f3efe6] px-2 py-0.5 text-[10px] font-medium text-[#6f6557]">
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#c9bfae]" /> Zugang nötig
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
      <h2 className="text-xl font-semibold">Der Talent-Pool dahinter</h2>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
        Ihr Commander besetzt jede Mission aus einem generativen Pool von{" "}
        <span className="font-semibold text-[#c25e0e]">{talentpoolFormatiert()}</span>{" "}
        adressierbaren Spezialisten-Profilen (Rolle × Fachgebiet × Branche ×
        Spezialisierung × Markt × Stufe). Jedes Profil ist über seine Nummer
        abrufbar und wird bei Bedarf instanziiert – rund um die Uhr, an jedem
        Tag. Sechs Beispiele aus dem Pool (Auswahl rotiert alle 30 Minuten,
        Stand {stand} Uhr):
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {beispiele.map((p) => (
          <div key={p.index} className="acc-card acc-card-hover rounded-2xl border-l-2 border-[#f472b6] p-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#be185d]/70">
              Profil #{p.index.toLocaleString("de-CH")}
            </p>
            <p className="mt-1.5 text-sm font-semibold text-[#be185d]">{p.titel}</p>
            <p className="mt-1 text-xs leading-relaxed text-[#6f6557]">
              {p.branche} · {p.spezialisierung} · Markt {p.markt}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 max-w-2xl text-xs leading-relaxed text-[#6f6557]">
        Ehrlich erklärt: Der Pool ist der Adressraum, aus dem live besetzt
        wird – nicht eine Milliarde gleichzeitig laufender Rechenprozesse.
        Wie viele Spezialisten pro Auftrag gleichzeitig rechnen, bestimmt
        Ihre Abo-Stufe (Tabelle oben). Genau diese Kombination macht das
        System gross UND schnell.
      </p>
    </section>
  );
}
