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
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b border-[#e8e1d2] bg-[#faf6ee]/80 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-2.5">
          <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
          <span className="text-sm font-bold">AI Command Center</span>
        </div>
        <WorkNav aktiv="agenten" variante="hell" />
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 pb-24 pt-6 sm:px-6">
        <div className="acc-in max-w-3xl">
          <p className="font-mono text-[11px] tracking-[0.22em] text-[#c25e0e]">{"// IHRE KI-BELEGSCHAFT"}</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            {AGENT_ANZAHL} Spezialisten-Agenten – ein <span className="acc-grad-text">Team</span> für alles
          </h1>
          <p className="mt-3 text-[15px] leading-relaxed text-[#6f6557]">
            Der Commander stellt für jede Mission das passende Team aus diesen benannten
            Spezialisten zusammen – und kann bei Bedarf jederzeit neue Agenten erschaffen.
            Kein Chatbot: eine ganze Organisation, die für Sie arbeitet.
          </p>
          <div className="mt-5 flex flex-wrap gap-2 text-[12px]">
            <span className="rounded-full border border-[#e8e1d2] bg-white/70 px-3 py-1 font-semibold text-[#4a4335]">
              {ABTEILUNGEN.length} Abteilungen
            </span>
            <span className="rounded-full border border-[#c7f0e6] bg-[#e6faf6] px-3 py-1 font-semibold text-[#0f766e]">
              {AGENT_ANZAHL} benannte Agenten
            </span>
            <span className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-3 py-1 font-semibold text-[#c25e0e]">
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
                  <span className="font-mono text-[11px] text-[#7c7161]">{agenten.length}</span>
                  <span className="h-px flex-1 bg-[#e8e1d2]" />
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {agenten.map((a) => (
                    <div
                      key={a.id}
                      className="acc-card acc-card-hover group rounded-2xl p-4"
                      style={{ borderTopColor: akzent, borderTopWidth: 2 }}
                    >
                      <div className="flex items-center gap-2">
                        <h3 className="text-[14px] font-semibold">{a.name}</h3>
                        {a.geplant && (
                          <span className="rounded-full border border-[#e0d8c6] px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-[#7c7161]">
                            geplant
                          </span>
                        )}
                      </div>
                      <p className="mt-1.5 text-[13px] leading-relaxed text-[#6f6557]">{a.aufgabe}</p>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {a.kann.map((k) => (
                          <span
                            key={k}
                            className="rounded-md border border-[#efe8da] bg-[#faf6ee] px-2 py-0.5 text-[11px] text-[#6b6152]"
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

        <div className="mt-12 rounded-2xl border border-[#ffb066]/30 bg-gradient-to-br from-[#fff4e6] to-white p-6 text-center">
          <h2 className="text-xl font-bold">Bereit, Ihr Team arbeiten zu lassen?</h2>
          <p className="mx-auto mt-2 max-w-xl text-[14px] text-[#6f6557]">
            Starten Sie eine Mission im Dashboard – der Commander besetzt automatisch die
            passenden Spezialisten – oder fragen Sie den KI-Chat direkt.
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <Link
              href="/dashboard"
              className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-[14px] font-bold text-white shadow-[0_6px_20px_-8px_rgba(255,110,30,0.6)]"
            >
              Mission starten
            </Link>
            <Link
              href="/assistent"
              className="rounded-xl border border-[#e0d8c6] bg-white/70 px-5 py-2.5 text-[14px] font-semibold text-[#4a4335] hover:border-[#ffb066]"
            >
              KI-Chat öffnen
            </Link>
          </div>
        </div>
      </main>

      <WorkFooter variante="hell" />
    </div>
  );
}
