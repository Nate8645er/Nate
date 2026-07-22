"use client";

/**
 * Integrations-Onboarding-Wizard: der Kunde wählt Schritt für Schritt selbst,
 * welche Systeme angebunden werden, und hinterlegt seine Firma. Am Ende wird
 * eine Anbindungs-Anfrage per E-Mail gestartet und der Firmenname lokal
 * gespeichert (erscheint danach im KI-Büro / Dashboard).
 *
 * Ehrlich: Die eigentliche, sichere Verbindung (OAuth wo möglich, verschlüsselte
 * Secrets) wird pro Unternehmen eingerichtet – dieser Assistent erfasst die
 * Auswahl und startet die Anfrage; er täuscht keine Live-Verbindung vor.
 */

import { useState } from "react";

const KONTAKT_EMAIL = "beamswiss@gmail.com";

const SYSTEME: { id: string; name: string; desc: string; c: string }[] = [
  { id: "m365", name: "Microsoft 365", desc: "Outlook, Teams, Word, Excel", c: "#1d63c9" },
  { id: "google", name: "Google Workspace", desc: "Gmail, Kalender, Docs, Sheets", c: "#0f766e" },
  { id: "slack", name: "Slack", desc: "Kanäle & Nachrichten", c: "#be185d" },
  { id: "notion", name: "Notion", desc: "Wissen & Dokumente", c: "#4a4335" },
  { id: "shopify", name: "Shopify", desc: "Shop, Bestellungen, Produkte", c: "#9a6b0f" },
  { id: "stripe", name: "Stripe", desc: "Zahlungen & Abos", c: "#5b52d6" },
  { id: "api", name: "Eigene API / Webhooks", desc: "Ihre Firmensoftware", c: "#7c3aed" },
  { id: "maschinen", name: "Produktionsmaschinen", desc: "IoT / Fertigung", c: "#c25e0e" },
];

const FOCUS = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ffb066]";
const INP = `w-full rounded-xl border border-[#e0d8c6] bg-white/70 px-3 py-2 text-sm text-[#1c1917] placeholder:text-[#a89c8a] focus:border-[#ffb066] focus:outline-none ${FOCUS}`;
const BTN_PRIMARY = `shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)] ${FOCUS}`;
const BTN_SEK = `rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2 text-sm font-semibold text-[#4a4335] hover:border-[#ffb066] ${FOCUS}`;

export default function OnboardingWizard() {
  const [offen, setOffen] = useState(false);
  const [schritt, setSchritt] = useState(1);
  const [gewaehlt, setGewaehlt] = useState<Set<string>>(new Set());
  const [firma, setFirma] = useState("");
  const [ansprech, setAnsprech] = useState("");
  const [fertig, setFertig] = useState(false);

  function reset() {
    setSchritt(1);
    setGewaehlt(new Set());
    setFirma("");
    setAnsprech("");
    setFertig(false);
  }
  function schliessen() {
    setOffen(false);
  }
  function toggle(id: string) {
    setGewaehlt((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  function anfragen() {
    const namen = SYSTEME.filter((s) => gewaehlt.has(s.id)).map((s) => s.name);
    try {
      if (firma.trim()) localStorage.setItem("acc-firma", firma.trim());
      localStorage.setItem("acc-connections", JSON.stringify([...gewaehlt]));
    } catch {
      /* Speicher voll/gesperrt – Anfrage geht trotzdem raus */
    }
    const subject = encodeURIComponent(`Anbindungs-Anfrage: ${firma.trim() || "Unternehmen"}`);
    const body = encodeURIComponent(
      `Guten Tag\n\nWir möchten folgende Systeme mit dem AI Command Center anbinden:\n` +
        namen.map((n) => `- ${n}`).join("\n") +
        `\n\nFirma: ${firma.trim()}\nAnsprechperson: ${ansprech.trim()}\n\n` +
        `Bitte richten Sie die sichere Anbindung ein (OAuth wo möglich).\n\nFreundliche Grüsse`,
    );
    try {
      window.location.href = `mailto:${KONTAKT_EMAIL}?subject=${subject}&body=${body}`;
    } catch {
      /* mailto nicht verfügbar */
    }
    setFertig(true);
  }

  const anzahl = gewaehlt.size;

  return (
    <>
      <button
        type="button"
        onClick={() => {
          reset();
          setOffen(true);
        }}
        className={BTN_PRIMARY}
      >
        Einrichtung starten →
      </button>

      {offen && (
        <div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-[#1c1917]/40 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Integrations-Einrichtung"
          onClick={schliessen}
        >
          <div
            className="acc-card acc-in mt-10 w-full max-w-2xl rounded-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
                  Einrichtung {fertig ? "· fertig" : `· Schritt ${schritt} von 3`}
                </p>
                <h2 className="mt-1 text-xl font-semibold tracking-tight">
                  {fertig
                    ? "Anfrage gestartet"
                    : schritt === 1
                      ? "Welche Systeme möchten Sie anbinden?"
                      : schritt === 2
                        ? "Ihre Firma"
                        : "Zusammenfassung"}
                </h2>
              </div>
              <button type="button" onClick={schliessen} aria-label="Schliessen" className={`rounded-lg px-2 py-1 text-[#8d8172] hover:text-[#1c1917] ${FOCUS}`}>
                ✕
              </button>
            </div>

            {/* Fortschritt */}
            {!fertig && (
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#efe9dd]" aria-hidden="true">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] transition-[width] duration-300"
                  style={{ width: `${(schritt / 3) * 100}%` }}
                />
              </div>
            )}

            {/* Inhalt */}
            <div className="mt-5">
              {fertig ? (
                <div className="text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#e7f6ee] text-[#177245]">
                    <svg viewBox="0 0 20 20" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                      <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <p className="mt-3 text-sm text-[#4a4335]">
                    Ihre Anbindungs-Anfrage für <span className="font-semibold">{firma.trim() || "Ihr Unternehmen"}</span> wurde
                    vorbereitet (E-Mail-Entwurf geöffnet). Wir richten die sichere Verbindung pro Unternehmen ein.
                  </p>
                  <p className="mt-2 text-xs text-[#8d8172]">
                    Ihr Firmenname erscheint jetzt im KI-Büro (Dashboard).
                  </p>
                  <div className="mt-5 flex justify-center gap-2">
                    <a href="/dashboard" className={BTN_PRIMARY}>Zum Dashboard</a>
                    <button type="button" onClick={schliessen} className={BTN_SEK}>Schliessen</button>
                  </div>
                </div>
              ) : schritt === 1 ? (
                <>
                  <p className="text-sm text-[#8d8172]">Mehrfachauswahl möglich – Sie können jederzeit weitere hinzufügen.</p>
                  <div className="mt-4 grid gap-2.5 sm:grid-cols-2">
                    {SYSTEME.map((s) => {
                      const an = gewaehlt.has(s.id);
                      return (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => toggle(s.id)}
                          aria-pressed={an}
                          className={`flex items-center gap-3 rounded-xl border p-3 text-left transition-colors ${FOCUS} ${
                            an ? "border-[#ffb066] bg-[#fff4e6]" : "border-[#e8e1d2] bg-white/60 hover:border-[#e0d8c6]"
                          }`}
                        >
                          <span
                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
                            style={{ background: s.c }}
                          >
                            {s.name.slice(0, 1)}
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block text-sm font-semibold text-[#1c1917]">{s.name}</span>
                            <span className="block truncate text-xs text-[#8d8172]">{s.desc}</span>
                          </span>
                          <span
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                              an ? "border-[#177245] bg-[#177245] text-white" : "border-[#d9cfbd] text-transparent"
                            }`}
                            aria-hidden="true"
                          >
                            ✓
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </>
              ) : schritt === 2 ? (
                <div className="grid gap-3">
                  <label className="block">
                    <span className="text-xs font-semibold text-[#8d8172]">Firmenname</span>
                    <input className={`${INP} mt-1`} value={firma} onChange={(e) => setFirma(e.target.value)} placeholder="z. B. Muster AG" autoFocus />
                  </label>
                  <label className="block">
                    <span className="text-xs font-semibold text-[#8d8172]">Ansprechperson (optional)</span>
                    <input className={`${INP} mt-1`} value={ansprech} onChange={(e) => setAnsprech(e.target.value)} placeholder="Name, E-Mail oder Telefon" />
                  </label>
                  <p className="rounded-xl bg-[#fff4e6] px-3 py-2 text-xs text-[#c25e0e]">
                    Der Firmenname erscheint anschliessend im KI-Büro. Wichtige/schreibende Schritte laufen nur mit Ihrer Freigabe.
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Gewählte Systeme</p>
                  {anzahl === 0 ? (
                    <p className="mt-2 text-sm text-[#8d8172]">Noch keine Systeme gewählt – gehen Sie zurück zu Schritt 1.</p>
                  ) : (
                    <ul className="mt-2 flex flex-wrap gap-2">
                      {SYSTEME.filter((s) => gewaehlt.has(s.id)).map((s) => (
                        <li key={s.id} className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-3 py-1 text-xs font-medium text-[#c25e0e]">
                          {s.name}
                        </li>
                      ))}
                    </ul>
                  )}
                  <p className="mt-4 text-sm text-[#4a4335]">
                    Firma: <span className="font-semibold">{firma.trim() || "—"}</span>
                    {ansprech.trim() && <> · Ansprechperson: {ansprech.trim()}</>}
                  </p>
                  <p className="mt-3 rounded-xl bg-[#faf6ee] px-3 py-2 text-xs leading-relaxed text-[#8d8172]">
                    Mit „Anbindung anfragen" öffnet sich ein E-Mail-Entwurf mit Ihrer Auswahl. Die sichere
                    Verbindung (OAuth wo möglich, verschlüsselte Zugänge) richten wir pro Unternehmen ein.
                  </p>
                </div>
              )}
            </div>

            {/* Navigation */}
            {!fertig && (
              <div className="mt-6 flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() => (schritt === 1 ? schliessen() : setSchritt((s) => s - 1))}
                  className={BTN_SEK}
                >
                  {schritt === 1 ? "Abbrechen" : "Zurück"}
                </button>
                {schritt < 3 ? (
                  <button
                    type="button"
                    onClick={() => setSchritt((s) => s + 1)}
                    disabled={schritt === 1 && anzahl === 0}
                    className={`${BTN_PRIMARY} disabled:cursor-not-allowed disabled:opacity-50`}
                  >
                    Weiter →
                  </button>
                ) : (
                  <button type="button" onClick={anfragen} disabled={anzahl === 0} className={`${BTN_PRIMARY} disabled:cursor-not-allowed disabled:opacity-50`}>
                    Anbindung anfragen
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
