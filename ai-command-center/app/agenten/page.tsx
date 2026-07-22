/**
 * Agenten-Übersicht – die komplette KI-Belegschaft der Plattform.
 *
 * Zeigt alle benannten Spezialisten-Agenten aus dem Roster, gruppiert nach
 * Abteilung, mit Aufgabe und konkreten Fähigkeiten. Statische Seite aus
 * echten Katalog-Daten (lib/agents/roster.ts) – kein Platzhalter.
 */

import Link from "next/link";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import {
  ABTEILUNGEN,
  ABTEILUNG_AKZENT,
  agentenNach,
  AGENT_ANZAHL,
} from "@/lib/agents/roster";

export const metadata = {
  title: "Agenten-Übersicht – AI Command Center",
  description: "Die komplette KI-Belegschaft: alle Spezialisten-Agenten und ihre Fähigkeiten.",
};

export default function AgentenPage() {
  return (
    <div className="min-h-screen bg-[#08070c] text-zinc-100">
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-[#ff8c2a] shadow-[0_0_10px_2px_rgba(255,140,42,0.7)]" />
          <span className="font-mono text-[11px] tracking-[0.22em] text-zinc-400">AI COMMAND CENTER</span>
        </div>
        <WorkNav aktiv="agenten" variante="dunkel" />
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 pb-24 pt-6 sm:px-6">
        <div className="max-w-3xl">
          <p className="font-mono text-[11px] tracking-[0.22em] text-[#ff8c2a]">// IHRE KI-BELEGSCHAFT</p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            {AGENT_ANZAHL} Spezialisten-Agenten – ein Team für alles
          </h1>
          <p className="mt-3 text-[15px] leading-relaxed text-zinc-400">
            Der Commander stellt für jede Mission das passende Team aus diesen benannten
            Spezialisten zusammen – und kann bei Bedarf jederzeit neue Agenten erschaffen.
            Kein Chatbot: eine ganze Organisation, die für Sie arbeitet.
          </p>
          <div className="mt-5 flex flex-wrap gap-2 text-[12px]">
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-zinc-300">
              {ABTEILUNGEN.length} Abteilungen
            </span>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-zinc-300">
              {AGENT_ANZAHL} benannte Agenten
            </span>
            <span className="rounded-full border border-[#ff8c2a]/30 bg-[#ff8c2a]/[0.08] px-3 py-1 text-[#ffb35c]">
              + dynamisch erweiterbar
            </span>
          </div>
        </div>

        <div className="mt-10 space-y-10">
          {ABTEILUNGEN.map((abt) => {
            const akzent = ABTEILUNG_AKZENT[abt];
            const agenten = agentenNach(abt);
            return (
              <section key={abt}>
                <div className="mb-4 flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full" style={{ background: akzent }} />
                  <h2 className="text-lg font-semibold tracking-tight">{abt}</h2>
                  <span className="font-mono text-[11px] text-zinc-500">{agenten.length}</span>
                  <span className="h-px flex-1 bg-white/8" />
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {agenten.map((a) => (
                    <div
                      key={a.id}
                      className="group rounded-2xl border border-white/8 bg-white/[0.03] p-4 transition-colors hover:border-white/15 hover:bg-white/[0.05]"
                      style={{ borderTopColor: akzent, borderTopWidth: 2 }}
                    >
                      <div className="flex items-center gap-2">
                        <h3 className="text-[14px] font-semibold text-white">{a.name}</h3>
                        {a.geplant && (
                          <span className="rounded-full border border-zinc-500/40 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-zinc-400">
                            geplant
                          </span>
                        )}
                      </div>
                      <p className="mt-1.5 text-[13px] leading-relaxed text-zinc-400">{a.aufgabe}</p>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {a.kann.map((k) => (
                          <span
                            key={k}
                            className="rounded-md bg-white/[0.05] px-2 py-0.5 text-[11px] text-zinc-300"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        <div className="mt-12 rounded-2xl border border-[#ff8c2a]/25 bg-gradient-to-br from-[#ff8c2a]/[0.08] to-transparent p-6 text-center">
          <h2 className="text-xl font-bold">Bereit, Ihr Team arbeiten zu lassen?</h2>
          <p className="mx-auto mt-2 max-w-xl text-[14px] text-zinc-400">
            Starten Sie eine Mission im Dashboard – der Commander besetzt automatisch die
            passenden Spezialisten – oder fragen Sie den KI-Chat direkt.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link
              href="/dashboard"
              className="rounded-xl bg-gradient-to-br from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-[14px] font-semibold text-white shadow-[0_6px_20px_-8px_rgba(255,110,30,0.6)]"
            >
              Mission starten
            </Link>
            <Link
              href="/assistent"
              className="rounded-xl border border-white/12 bg-white/[0.04] px-5 py-2.5 text-[14px] font-medium text-zinc-200 hover:bg-white/[0.07]"
            >
              KI-Chat öffnen
            </Link>
          </div>
        </div>
      </main>

      <WorkFooter variante="dunkel" />
    </div>
  );
}
