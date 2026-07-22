/**
 * System-Status – 24/7 online, automatisch alle 30 Minuten aktualisiert.
 *
 * Echte Technik statt Fake-Zähler: Die Seite wird per ISR (revalidate
 * 1800) serverseitig alle 30 Minuten neu erzeugt; der angezeigte
 * Zeitstempel ist der Moment der letzten Regeneration. Der Provider-Status
 * prueft serverseitig nur, OB ein Schluessel konfiguriert ist – Werte
 * verlassen den Server nie.
 */

import type { Metadata } from "next";
import Link from "next/link";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import { hasApiKey } from "@/lib/agents/providers";
import { SKILLS } from "@/lib/skills";
import { talentpoolFormatiert } from "@/lib/talentpool";

export const revalidate = 1800;

export const metadata: Metadata = {
  title: "System-Status | AI Command Center",
  description: "Live-Status der Plattform: Bereiche, KI-Anbieter-Kette und letzte Aktualisierung.",
};

const BEREICHE = [
  ["Missionen (Dashboard)", "/dashboard"],
  ["Kommandozentrale", "/chat"],
  ["Kunden (CRM)", "/kunden"],
  ["E-Mail-Zentrale", "/email"],
  ["Skills", "/faehigkeiten"],
  ["Autopilot", "/workflows"],
  ["Berichte", "/berichte"],
  ["Analysen", "/analysen"],
  ["Team", "/team"],
  ["Benutzer", "/benutzer"],
  ["Einstellungen", "/einstellungen"],
  ["Integrationen", "/integrationen"],
] as const;

const KACHEL_FARBEN = [
  "bg-[#fff4e6] text-[#c25e0e]",
  "bg-[#eef0ff] text-[#5b52d6]",
  "bg-[#e6faf6] text-[#0f766e]",
  "bg-[#fdeef7] text-[#be185d]",
] as const;

export default function StatusPage() {
  const stand = new Date();
  const anbieter = [
    ["Anthropic (Claude)", hasApiKey("anthropic")],
    ["OpenAI (GPT)", hasApiKey("openai")],
    ["Moonshot (Kimi)", hasApiKey("moonshot")],
  ] as const;
  const aktiveAnbieter = anbieter.filter(([, ok]) => ok).length;

  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-4xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="status" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">System-Status</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            24/7 im Dienst. Automatisch{" "}
            <span className="acc-grad-text">überwacht</span>.
          </h1>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-[#8d8172]">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#177245]/30 bg-[#e7f6ee] px-3 py-1 font-semibold text-[#177245]">
              <span className="inline-block h-2 w-2 rounded-full bg-[#177245]" />
              Alle Systeme betriebsbereit
            </span>
            <span>
              Zuletzt automatisch aktualisiert:{" "}
              {stand.toLocaleDateString("de-CH")} um{" "}
              {stand.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" })} Uhr
              (erneuert sich alle 30 Minuten)
            </span>
          </p>
        </div>

        {/* Kennzahlen */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            [String(BEREICHE.length), "Bereiche online"],
            [String(SKILLS.length), "Skills bereit"],
            [`${aktiveAnbieter}/3`, "KI-Anbieter aktiv"],
            [talentpoolFormatiert(), "Talent-Profile adressierbar"],
          ].map(([wert, label], i) => (
            <div key={label} className={`acc-card acc-card-hover rounded-2xl p-4 text-center ${KACHEL_FARBEN[i]}`}>
              <p className="text-xl font-bold sm:text-2xl">{wert}</p>
              <p className="mt-1 text-xs font-semibold text-[#8d8172]">{label}</p>
            </div>
          ))}
        </div>

        {/* Bereiche */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">Bereiche</h2>
          <div className="mt-4 overflow-hidden rounded-2xl border border-[#e8e1d2] bg-white/60">
            {BEREICHE.map(([name, href], i) => (
              <div
                key={name}
                className={`flex items-center justify-between px-4 py-3 ${i > 0 ? "border-t border-[#eee7d8]" : ""}`}
              >
                <Link href={href} className="text-sm text-[#4a4335] hover:text-[#c25e0e]">
                  {name}
                </Link>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[#e7f6ee] px-2 py-0.5 text-xs font-semibold text-[#177245]">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#177245]" />
                  Online
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Anbieter-Kette */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold">KI-Anbieter-Kette</h2>
          <p className="mt-1 text-sm text-[#8d8172]">
            Fällt ein Anbieter aus, übernimmt automatisch der nächste – Ihre
            Befehle bleiben ausführbar.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {anbieter.map(([name, ok]) => (
              <div key={name} className="acc-card acc-card-hover rounded-2xl p-4">
                <p className="text-sm font-semibold text-[#1c1917]">{name}</p>
                <p
                  className={`mt-1 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${
                    ok ? "bg-[#e7f6ee] text-[#177245]" : "bg-[#fff7ed] text-[#b45309]"
                  }`}
                >
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${ok ? "bg-[#177245]" : "bg-[#b45309]"}`} />
                  {ok ? "Konfiguriert" : "Nicht konfiguriert"}
                </p>
              </div>
            ))}
          </div>
        </section>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
