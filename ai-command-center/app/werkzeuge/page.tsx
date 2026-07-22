"use client";

/**
 * Blitz-Werkzeuge – echte Werkzeuge, die SOFORT ein fertiges Ergebnis
 * liefern (ohne KI, ohne Warten): Berechnung/Erzeugung im Browser in
 * Millisekunden. Genau das, was in Sekunden erledigt sein soll.
 */

import { useMemo, useState } from "react";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import {
  ibanPruefen,
  passwortErzeugen,
  rechnungHtml,
  rechnungSumme,
  chf,
  marge,
  stundensatz,
  signaturHtml,
  slug,
  type Position,
} from "@/lib/blitz";

function download(name: string, inhalt: string, typ = "text/html") {
  const blob = new Blob([inhalt], { type: `${typ};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

const card = "acc-card rounded-2xl p-5";
const inp = "w-full rounded-xl border border-[#e0d8c6] bg-white/70 px-3 py-2 text-sm focus:border-[#ffb066] focus:outline-none";
const btn = "shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]";
const lbl = "text-xs font-semibold text-[#8d8172]";

export default function WerkzeugePage() {
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="werkzeuge" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Blitz-Werkzeuge</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Echte Arbeit. In Sekunden erledigt.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#8d8172]">
            Diese Werkzeuge rechnen und erzeugen sofort – direkt in Ihrem Browser,
            ohne Warten. Keine Vorschau, echte Ergebnisse: geprüfte IBANs,
            versandfertige Rechnungen, sichere Passwörter, fertige Signaturen.
          </p>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-2">
          <IbanTool />
          <PasswortTool />
          <RechnungTool />
          <MargeTool />
          <StundensatzTool />
          <SignaturTool />
          <SlugTool />
        </div>

        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}

function IbanTool() {
  const [iban, setIban] = useState("");
  const r = useMemo(() => (iban.trim() ? ibanPruefen(iban) : null), [iban]);
  return (
    <section className={card}>
      <h2 className="font-semibold">IBAN prüfen</h2>
      <p className="mt-1 text-xs text-[#8d8172]">Sofort geprüft (Modulo-97, ISO 13616).</p>
      <input aria-label="IBAN" className={`${inp} mt-3 font-mono`} placeholder="CH93 0076 2011 6238 5295 7" value={iban} onChange={(e) => setIban(e.target.value)} />
      {r && (
        <p className={`mt-3 rounded-xl px-3 py-2 text-sm font-semibold ${r.valid ? "bg-[#e7f6ee] text-[#177245]" : "bg-red-50 text-red-600"}`}>
          {r.valid ? `✓ Gültig (${r.land}) · ${r.formatiert}` : "✕ Ungültige IBAN"}
        </p>
      )}
    </section>
  );
}

function PasswortTool() {
  const [laenge, setLaenge] = useState(16);
  const [zeichen, setZeichen] = useState(true);
  const [pw, setPw] = useState("");
  const erzeugen = () => setPw(passwortErzeugen({ laenge, gross: true, klein: true, zahlen: true, zeichen }));
  return (
    <section className={card}>
      <h2 className="font-semibold">Sicheres Passwort</h2>
      <p className="mt-1 text-xs text-[#8d8172]">Kryptographisch zufällig, sofort.</p>
      <div className="mt-3 flex items-center gap-3">
        <label className={lbl}>Länge {laenge}</label>
        <input aria-label="Länge" type="range" min={8} max={40} value={laenge} onChange={(e) => setLaenge(Number(e.target.value))} className="flex-1 accent-[#ff8c2a]" />
      </div>
      <label className="mt-2 flex items-center gap-2 text-sm">
        <input type="checkbox" checked={zeichen} onChange={(e) => setZeichen(e.target.checked)} className="accent-[#ff8c2a]" /> Sonderzeichen
      </label>
      <div className="mt-3 flex gap-2">
        <button className={btn} onClick={erzeugen}>Erzeugen</button>
        {pw && <code className="flex-1 truncate rounded-xl border border-[#e0d8c6] bg-white/70 px-3 py-2 font-mono text-sm">{pw}</code>}
      </div>
      {pw && <button className="mt-2 text-xs font-semibold text-[#c25e0e] hover:underline" onClick={() => navigator.clipboard?.writeText(pw)}>Kopieren</button>}
    </section>
  );
}

function RechnungTool() {
  const [empfaenger, setEmpfaenger] = useState("");
  const [positionen, setPositionen] = useState<Position[]>([{ text: "", menge: 1, einzelpreis: 0 }]);
  const [mwst, setMwst] = useState(8.1);
  const s = rechnungSumme(positionen, mwst);
  const setPos = (i: number, patch: Partial<Position>) =>
    setPositionen((p) => p.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const laden = () => {
    const html = rechnungHtml({
      absender: "Ihre Firma\nStrasse 1\n8000 Zürich",
      empfaenger: empfaenger || "Kunde",
      nummer: `R-${new Date().getFullYear()}-${String(Math.floor(Date.now() / 1000) % 10000).padStart(4, "0")}`,
      datum: new Date().toLocaleDateString("de-CH"),
      positionen: positionen.filter((p) => p.text.trim()),
      mwstSatz: mwst,
      frist: "30",
    });
    download("Rechnung.html", html);
  };
  return (
    <section className={`${card} md:col-span-2`}>
      <h2 className="font-semibold">Rechnung erstellen</h2>
      <p className="mt-1 text-xs text-[#8d8172]">Positionen eintragen → fertige HTML-Rechnung herunterladen (druck-/PDF-fähig).</p>
      <input aria-label="Empfänger" className={`${inp} mt-3`} placeholder="Empfänger (Name, Firma)" value={empfaenger} onChange={(e) => setEmpfaenger(e.target.value)} />
      <div className="mt-3 space-y-2">
        {positionen.map((p, i) => (
          <div key={i} className="grid grid-cols-[1fr_60px_90px] gap-2">
            <input aria-label={`Leistung ${i + 1}`} className={inp} placeholder="Leistung" value={p.text} onChange={(e) => setPos(i, { text: e.target.value })} />
            <input aria-label={`Menge ${i + 1}`} className={inp} type="number" value={p.menge} onChange={(e) => setPos(i, { menge: Number(e.target.value) })} />
            <input aria-label={`Preis ${i + 1}`} className={inp} type="number" placeholder="CHF" value={p.einzelpreis} onChange={(e) => setPos(i, { einzelpreis: Number(e.target.value) })} />
          </div>
        ))}
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <button className="text-xs font-semibold text-[#c25e0e] hover:underline" onClick={() => setPositionen((p) => [...p, { text: "", menge: 1, einzelpreis: 0 }])}>+ Position</button>
        <label className={lbl}>MwSt %</label>
        <input aria-label="MwSt" className={`${inp} w-20`} type="number" step="0.1" value={mwst} onChange={(e) => setMwst(Number(e.target.value))} />
        <span className="ml-auto text-sm font-semibold">Total: CHF {chf(s.brutto)}</span>
        <button className={btn} onClick={laden}>Rechnung herunterladen</button>
      </div>
    </section>
  );
}

function MargeTool() {
  const [ek, setEk] = useState(0);
  const [vk, setVk] = useState(0);
  const m = marge(ek, vk);
  return (
    <section className={card}>
      <h2 className="font-semibold">Marge & Aufschlag</h2>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <div><label className={lbl}>Einkauf CHF</label><input aria-label="Einkauf" className={inp} type="number" value={ek} onChange={(e) => setEk(Number(e.target.value))} /></div>
        <div><label className={lbl}>Verkauf CHF</label><input aria-label="Verkauf" className={inp} type="number" value={vk} onChange={(e) => setVk(Number(e.target.value))} /></div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div className="rounded-xl bg-[#fff4e6] py-2"><p className="text-lg font-bold text-[#c25e0e]">{chf(m.gewinn)}</p><p className="text-[10px] text-[#8d8172]">Gewinn</p></div>
        <div className="rounded-xl bg-[#fff4e6] py-2"><p className="text-lg font-bold text-[#c25e0e]">{m.margeProz}%</p><p className="text-[10px] text-[#8d8172]">Marge</p></div>
        <div className="rounded-xl bg-[#fff4e6] py-2"><p className="text-lg font-bold text-[#c25e0e]">{m.aufschlagProz}%</p><p className="text-[10px] text-[#8d8172]">Aufschlag</p></div>
      </div>
    </section>
  );
}

function StundensatzTool() {
  const [jk, setJk] = useState(120000);
  const [std, setStd] = useState(1200);
  const [m, setM] = useState(20);
  const satz = stundensatz(jk, std, m);
  return (
    <section className={card}>
      <h2 className="font-semibold">Stundensatz</h2>
      <p className="mt-1 text-xs text-[#8d8172]">Kostendeckend inkl. Zielmarge.</p>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <div><label className={lbl}>Jahreskosten</label><input aria-label="Jahreskosten" className={inp} type="number" value={jk} onChange={(e) => setJk(Number(e.target.value))} /></div>
        <div><label className={lbl}>Fakt. Std/Jahr</label><input aria-label="Stunden" className={inp} type="number" value={std} onChange={(e) => setStd(Number(e.target.value))} /></div>
        <div><label className={lbl}>Marge %</label><input aria-label="Marge Prozent" className={inp} type="number" value={m} onChange={(e) => setM(Number(e.target.value))} /></div>
      </div>
      <p className="mt-3 rounded-xl bg-[#e7f6ee] px-3 py-2 text-center text-lg font-bold text-[#177245]">CHF {chf(satz)} / Stunde</p>
    </section>
  );
}

function SignaturTool() {
  const [f, setF] = useState({ name: "", rolle: "", firma: "", tel: "", mail: "", web: "" });
  const html = signaturHtml(f);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value });
  return (
    <section className={`${card} md:col-span-2`}>
      <h2 className="font-semibold">E-Mail-Signatur</h2>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        <input aria-label="Name" className={inp} placeholder="Name" value={f.name} onChange={set("name")} />
        <input aria-label="Rolle" className={inp} placeholder="Rolle" value={f.rolle} onChange={set("rolle")} />
        <input aria-label="Firma" className={inp} placeholder="Firma" value={f.firma} onChange={set("firma")} />
        <input aria-label="Telefon" className={inp} placeholder="Telefon" value={f.tel} onChange={set("tel")} />
        <input aria-label="E-Mail" className={inp} placeholder="E-Mail" value={f.mail} onChange={set("mail")} />
        <input aria-label="Web" className={inp} placeholder="Website" value={f.web} onChange={set("web")} />
      </div>
      {f.name && (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-[#e0d8c6] bg-white p-3" dangerouslySetInnerHTML={{ __html: html }} />
          <button className={btn} onClick={() => navigator.clipboard?.writeText(html)}>HTML kopieren</button>
        </div>
      )}
    </section>
  );
}

function SlugTool() {
  const [t, setT] = useState("");
  const r = t.trim() ? slug(t) : null;
  return (
    <section className={card}>
      <h2 className="font-semibold">SEO-Slug & Titel</h2>
      <input aria-label="Text" className={`${inp} mt-3`} placeholder="z. B. Offerte für Zürich" value={t} onChange={(e) => setT(e.target.value)} />
      {r && (
        <div className="mt-3 space-y-1 text-sm">
          <p><span className={lbl}>Slug: </span><code className="font-mono text-[#c25e0e]">{r.slug}</code></p>
          <p><span className={lbl}>Titel: </span>{r.titel}</p>
        </div>
      )}
    </section>
  );
}
