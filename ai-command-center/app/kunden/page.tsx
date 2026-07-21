"use client";

/**
 * Kunden – Mini-CRM mit Pipeline, verbunden mit dem Rest des Systems.
 *
 * Recherche-Ergebnis (2026): KMU brauchen vor allem Kontaktverwaltung mit
 * Pipeline und die nahtlose Verknüpfung der Werkzeuge. Genau das hier:
 * - Kunden mit Status-Pipeline (Lead -> Offerte offen -> Kunde)
 * - Pro Kunde direkt: E-Mail schreiben (E-Mail-Zentrale, Empfänger
 *   vorbefüllt) und Offerte erstellen (Kommandozentrale, Befehl vorbefüllt)
 * - Notizen pro Kunde; Daten lokal (acc-kunden), Export über /einstellungen
 *
 * Ehrlich: zentrales Firmen-CRM mit Sync über alle Geräte/Mitarbeitenden
 * ist Teil der Enterprise-Einrichtung (steht im UI).
 */

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import WorkNav from "@/app/components/WorkNav";

const KUNDEN_KEY = "acc-kunden";

type Status = "Lead" | "Offerte offen" | "Kunde";

interface Kunde {
  id: string;
  name: string;
  firma: string;
  email: string;
  status: Status;
  notiz: string;
}

const STATUS_REIHENFOLGE: Status[] = ["Lead", "Offerte offen", "Kunde"];
const STATUS_FARBE: Record<Status, string> = {
  Lead: "bg-[#ede9fe] text-[#6d28d9] border-[#ddd6fe]",
  "Offerte offen": "bg-[#fff4e6] text-[#c25e0e] border-[#fcdcb5]",
  Kunde: "bg-[#e7f6ee] text-[#177245] border-[#c6ecd7]",
};

export default function KundenPage() {
  const [kunden, setKunden] = useState<Kunde[]>([]);
  const [name, setName] = useState("");
  const [firma, setFirma] = useState("");
  const [email, setEmail] = useState("");
  const [offenNotiz, setOffenNotiz] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KUNDEN_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Kunde[];
        if (Array.isArray(parsed)) setKunden(parsed);
      }
    } catch {
      /* Storage nicht lesbar */
    }
  }, []);

  const persist = useCallback((next: Kunde[]) => {
    setKunden(next);
    try {
      localStorage.setItem(KUNDEN_KEY, JSON.stringify(next));
    } catch {
      /* voll */
    }
  }, []);

  const hinzufuegen = () => {
    const n = name.trim().slice(0, 60);
    if (!n) return;
    persist([
      {
        id: `c${Date.now().toString(36)}`,
        name: n,
        firma: firma.trim().slice(0, 80),
        email: email.trim().slice(0, 120),
        status: "Lead",
        notiz: "",
      },
      ...kunden,
    ]);
    setName("");
    setFirma("");
    setEmail("");
  };

  /** Verbindung 1: Offerte in der Kommandozentrale, Befehl vorbefüllt. */
  const offerteLink = (k: Kunde) =>
    `/chat?text=${encodeURIComponent(
      `Erstelle eine vollständige, versandfertige Offerte als Dokument für ${k.name}${k.firma ? ` (${k.firma})` : ""}: Leistung [was wird angeboten], Preis [Betrag] CHF, Lieferzeit [Dauer], Zahlungsbedingungen, Gültigkeit 30 Tage.`,
    )}`;

  /** Verbindung 2: E-Mail-Zentrale mit vorbefülltem Empfänger. */
  const emailLink = (k: Kunde) =>
    `/email?an=${encodeURIComponent(k.email)}&auftrag=${encodeURIComponent(
      `E-Mail an ${k.name}${k.firma ? ` von ${k.firma}` : ""}: [worum geht es]`,
    )}`;

  const zaehler = (s: Status) => kunden.filter((k) => k.status === s).length;

  return (
    <div className="min-h-dvh bg-[#faf8f3] text-[#241f17]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="kunden" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Kundenverwaltung</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Ihre Kunden. Verbunden mit Ihrer Belegschaft.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#8d8172]">
            Vom Lead bis zum Kunden: Kontakte verwalten und direkt handeln –
            ein Klick, und Ihre KI schreibt die E-Mail oder erstellt die
            Offerte für genau diesen Kunden. Rechnungen und Mahnungen:{" "}
            <Link href="/chat?befehl=%2Frechnung" className="font-medium text-[#c25e0e] hover:underline">/rechnung</Link>{" "}
            und{" "}
            <Link href="/chat?befehl=%2Fmahnung" className="font-medium text-[#c25e0e] hover:underline">/mahnung</Link>.
          </p>
          <p className="mt-3 max-w-2xl rounded-xl border border-[#f0ceA0] bg-[#fff4e6] px-4 py-3 text-xs leading-relaxed text-[#8a4a12]">
            Transparenz: Kundendaten liegen in diesem Browser (Export unter
            Einstellungen). Zentrales Firmen-CRM mit Sync für alle
            Mitarbeitenden richten wir als Enterprise-Projekt ein.
          </p>
        </div>

        {/* Pipeline-Zähler */}
        <div className="mt-8 grid grid-cols-3 gap-4">
          {STATUS_REIHENFOLGE.map((s) => (
            <div key={s} className="rounded-2xl border border-[#eee7d8] bg-white p-4 text-center shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
              <p className="text-2xl font-bold text-[#c25e0e]">{zaehler(s)}</p>
              <p className="mt-0.5 text-xs font-medium text-[#8d8172]">{s}</p>
            </div>
          ))}
        </div>

        {/* Neu erfassen */}
        <form
          className="mt-6 grid gap-3 rounded-2xl border border-[#eee7d8] bg-white p-5 shadow-[0_1px_3px_rgba(40,30,10,0.05)] sm:grid-cols-[1fr_1fr_1fr_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            hinzufuegen();
          }}
        >
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name *"
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none" aria-label="Name" />
          <input value={firma} onChange={(e) => setFirma(e.target.value)} placeholder="Firma"
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none" aria-label="Firma" />
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="E-Mail"
            className="rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-2.5 text-sm focus:border-[#ffb066] focus:outline-none" aria-label="E-Mail" />
          <button type="submit" disabled={!name.trim()}
            className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-40">
            + Kunde
          </button>
        </form>

        {/* Liste */}
        <div className="mt-6 space-y-3">
          {kunden.length === 0 && (
            <p className="rounded-2xl border border-[#eee7d8] bg-white px-5 py-10 text-center text-sm text-[#8d8172]">
              Noch keine Kunden erfasst. Beginnen Sie mit Ihrem wichtigsten Lead.
            </p>
          )}
          {kunden.map((k) => (
            <article key={k.id} className="rounded-2xl border border-[#eee7d8] bg-white p-5 shadow-[0_1px_3px_rgba(40,30,10,0.05)]">
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f] font-bold text-white">
                  {k.name.slice(0, 1).toUpperCase()}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-semibold">
                    {k.name}
                    {k.firma && <span className="font-normal text-[#8d8172]"> · {k.firma}</span>}
                  </p>
                  {k.email && <p className="truncate text-xs text-[#a2988a]">{k.email}</p>}
                </div>
                <select
                  value={k.status}
                  onChange={(e) =>
                    persist(kunden.map((x) => (x.id === k.id ? { ...x, status: e.target.value as Status } : x)))
                  }
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold focus:outline-none ${STATUS_FARBE[k.status]}`}
                  aria-label={`Status von ${k.name}`}
                >
                  {STATUS_REIHENFOLGE.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Link href={emailLink(k)}
                  className="shop-btn rounded-lg bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-3.5 py-2 text-xs font-bold text-white">
                  ✉ E-Mail schreiben lassen
                </Link>
                <Link href={offerteLink(k)}
                  className="shop-btn rounded-lg border border-[#f0ceA0] bg-[#fff4e6] px-3.5 py-2 text-xs font-bold text-[#8a4a12]">
                  📄 Offerte erstellen lassen
                </Link>
                <button
                  onClick={() => setOffenNotiz(offenNotiz === k.id ? null : k.id)}
                  className="rounded-lg border border-[#e0d8c6] px-3.5 py-2 text-xs text-[#6f6557] hover:border-[#ffb066]"
                >
                  Notiz
                </button>
                <button
                  onClick={() => persist(kunden.filter((x) => x.id !== k.id))}
                  className="ml-auto rounded-lg border border-[#e0d8c6] px-3 py-2 text-xs text-[#a2988a] hover:border-red-300 hover:text-red-600"
                  aria-label={`${k.name} löschen`}
                >
                  ✕
                </button>
              </div>

              {offenNotiz === k.id && (
                <textarea
                  value={k.notiz}
                  onChange={(e) =>
                    persist(kunden.map((x) => (x.id === k.id ? { ...x, notiz: e.target.value.slice(0, 2000) } : x)))
                  }
                  rows={3}
                  placeholder="Notizen zu diesem Kunden … (letztes Gespräch, Bedürfnisse, nächster Schritt)"
                  className="mt-3 w-full resize-none rounded-xl border border-[#e0d8c6] bg-[#faf8f3] px-4 py-3 text-sm focus:border-[#ffb066] focus:outline-none"
                  aria-label={`Notiz zu ${k.name}`}
                />
              )}
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
