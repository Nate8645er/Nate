import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { PAKETE, VERGLEICH, chf } from "@/lib/preise";
import { SKILLS, SKILL_KATEGORIEN, skillVerfuegbar, skillAnzahlFuer } from "@/lib/skills";

export function generateStaticParams() {
  return PAKETE.map((p) => ({ id: p.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const p = PAKETE.find((x) => x.id === id);
  if (!p) return { title: "Paket – AI Command Center" };
  return {
    title: `${p.name} – AI Command Center`,
    description: p.untertitel,
  };
}

export default async function ProduktSeite({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const paket = PAKETE.find((p) => p.id === id);
  if (!paket) notFound();

  // Echter Fähigkeiten-Katalog, gefiltert auf die Abo-Stufe dieses Pakets.
  const verfuegbar = SKILLS.filter((s) => skillVerfuegbar(s.befehl, paket.planId));
  const anzahlSkills = skillAnzahlFuer(paket.planId);
  const nachKategorie = SKILL_KATEGORIEN.map((k) => ({
    kat: k,
    skills: verfuegbar.filter((s) => s.kategorie === k),
  })).filter((g) => g.skills.length > 0);

  return (
    <main className="bg-[#fdfbf7] text-[#1c1917]">
      {/* Hero */}
      <section className="acc-hero-dark relative overflow-hidden px-6 py-24">
        <div className="acc-hero-glow" aria-hidden="true" />
        <div className="relative mx-auto max-w-4xl">
          <Link href="/preise" className="text-sm font-medium text-[#b9b7d4] hover:text-white">
            ← Alle Pakete
          </Link>
          <p className="mt-6 text-[11px] font-bold uppercase tracking-[0.28em] text-[#c9c6ff]">
            {paket.zielgruppe}
          </p>
          <h1 className="mt-2 text-4xl font-extrabold tracking-tight text-white sm:text-6xl">
            <span className="acc-grad-text">{paket.name}</span>
          </h1>
          <p className="mt-4 max-w-xl text-lg text-[#b9b7d4]">{paket.untertitel}</p>
          <div className="mt-8 flex flex-wrap items-end gap-4">
            <div className="text-3xl font-extrabold text-white">
              {paket.preisMonat <= 0 ? "Gratis" : chf(paket.preisMonat)}
              {paket.preisMonat > 0 && <span className="text-base font-medium text-[#b9b7d4]"> / Monat</span>}
            </div>
            <Link
              href="/preise"
              className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-6 py-3 text-sm font-bold text-white shadow-[0_10px_28px_-8px_rgba(255,110,30,0.6)] hover:brightness-105"
            >
              {paket.cta}
            </Link>
          </div>
        </div>
      </section>

      {/* Leistungen */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-bold">Das ist in {paket.name} enthalten</h2>
          <ul className="mt-6 grid gap-3 sm:grid-cols-2">
            {paket.leistungen.map((l) => (
              <li key={l} className="acc-card flex items-start gap-3 rounded-2xl p-4">
                <svg viewBox="0 0 20 20" className="mt-0.5 h-5 w-5 shrink-0 text-[#177245]" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <span className="text-sm text-[#4a4335]">{l}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Was die KI-Abteilung alles kann (echter Skill-Katalog je Stufe) */}
      <section className="border-t border-[#e8e1d2] bg-[#faf6ee] px-6 py-16">
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <h2 className="text-2xl font-bold">
              Was Ihre KI-Abteilung im <span className="acc-grad-text">{paket.name}</span> alles kann
            </h2>
            <span className="rounded-full border border-[#ffb066]/50 bg-[#fff4e6] px-3 py-1 text-sm font-bold text-[#c25e0e]">
              {anzahlSkills}+ Fähigkeiten freigeschaltet
            </span>
          </div>
          <p className="mt-2 max-w-2xl text-sm text-[#6f6557]">
            Jede Fähigkeit ist ein fertiger Auftrag – ein Klick oder Befehl, und Ihre
            Belegschaft liefert ein geprüftes Ergebnis. Auswahl nach Bereich:
          </p>

          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {nachKategorie.map((g) => (
              <div key={g.kat} className="acc-card rounded-2xl p-5">
                <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
                  {g.kat} · {g.skills.length}
                </p>
                <ul className="mt-3 space-y-2.5">
                  {g.skills.map((s) => (
                    <li key={s.befehl}>
                      <p className="text-sm font-semibold text-[#1c1917]">{s.name}</p>
                      <p className="text-xs leading-relaxed text-[#6f6557]">{s.beschreibung}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Einordnung im Vergleich */}
      <section className="border-t border-[#e8e1d2] px-6 py-16">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-2xl font-bold">So schneidet {paket.name} ab</h2>
          <div className="mt-6 space-y-6">
            {VERGLEICH.map((g) => {
              const idx = PAKETE.findIndex((p) => p.id === paket.id);
              return (
                <div key={g.gruppe}>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">{g.gruppe}</p>
                  <ul className="mt-2 divide-y divide-[#efe9dd]">
                    {g.zeilen.map((z) => (
                      <li key={z.label} className="flex items-center justify-between gap-4 py-2 text-sm">
                        <span className="text-[#6f6557]">{z.label}</span>
                        <span className="font-semibold text-[#1c1917]">{z.werte[idx]}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
          <div className="mt-10 text-center">
            <Link
              href="/preise"
              className="rounded-full border border-[#e0d8c6] bg-white px-6 py-3 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]"
            >
              Pakete vergleichen
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
