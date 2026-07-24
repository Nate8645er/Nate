import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Kontakt – AI Command Center",
  description:
    "Sprechen Sie mit uns über Ihre KI-Abteilung – Beratung, Enterprise-Anfragen und individuelle Integrationen.",
};

const THEMEN = [
  {
    titel: "Vertrieb & Beratung",
    text: "Welches Paket passt zu Ihrer Firma? Wir beraten Sie unverbindlich.",
    betreff: "Beratung AI Command Center",
    cta: "Beratung anfragen",
  },
  {
    titel: "Enterprise & On-Premise",
    text: "Individuelle KI-Infrastruktur, SSO, private Cloud oder On-Premise.",
    betreff: "Enterprise-Anfrage AI Command Center",
    cta: "Enterprise anfragen",
  },
  {
    titel: "Support",
    text: "Fragen zu Ihrem bestehenden Zugang oder zur Einrichtung.",
    betreff: "Support AI Command Center",
    cta: "Support kontaktieren",
  },
];

export default function KontaktSeite() {
  return (
    <main className="bg-[#fdfbf7] text-[#1c1917]">
      <section className="acc-hero-dark relative overflow-hidden px-6 py-24 text-center">
        <div className="acc-hero-glow" aria-hidden="true" />
        <div className="relative mx-auto max-w-2xl">
          <p className="mb-4 text-[11px] font-bold uppercase tracking-[0.28em] text-[#c9c6ff]">Kontakt</p>
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            Sprechen wir über Ihre <span className="acc-grad-text">KI-Abteilung</span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg text-[#b9b7d4]">
            Wir melden uns in der Regel innerhalb eines Werktags.
          </p>
        </div>
      </section>

      <section className="px-6 py-16">
        <div className="mx-auto grid max-w-5xl gap-6 sm:grid-cols-3">
          {THEMEN.map((t) => (
            <div key={t.titel} className="acc-card flex flex-col rounded-2xl p-6">
              <h2 className="text-lg font-bold">{t.titel}</h2>
              <p className="mt-2 flex-1 text-sm text-[#6f6557]">{t.text}</p>
              <a
                href={`mailto:kontakt@ihre-domain.ch?subject=${encodeURIComponent(t.betreff)}`}
                className="mt-4 inline-block rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-center text-sm font-bold text-white hover:brightness-105"
              >
                {t.cta}
              </a>
            </div>
          ))}
        </div>
        <p className="mx-auto mt-8 max-w-2xl text-center text-sm text-[#6f6557]">
          Oder schauen Sie sich zuerst die <Link href="/preise" className="font-semibold text-[#c25e0e] hover:underline">Pakete &amp; Preise</Link> an.
          Die E-Mail-Adresse in <code>app/kontakt/page.tsx</code> auf Ihre eigene anpassen.
        </p>
      </section>
    </main>
  );
}
