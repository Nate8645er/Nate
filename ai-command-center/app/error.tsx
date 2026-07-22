"use client";

/**
 * Globale Fehlerseite (App-Router error boundary).
 *
 * Faengt unerwartete Fehler in allen Bereichen ab und zeigt statt eines
 * weissen Bildschirms eine professionelle Meldung mit zwei Wegen:
 * "Erneut versuchen" (reset) und "Fehler melden" – der Bericht geht mit
 * technischen Details (Fehlermeldung, Seite, Zeitpunkt, Browser) per
 * E-Mail an den Betreiber, der ihn zur Behebung weiterleiten kann.
 */

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Serverseitig loggt Next selbst; hier fuer die Browser-Konsole.
    console.error("[acc-fehler]", error);
  }, [error]);

  const bericht = [
    "Fehlerbericht AI Command Center",
    `Zeitpunkt: ${new Date().toLocaleString("de-CH")}`,
    `Seite: ${typeof window !== "undefined" ? window.location.pathname : "?"}`,
    `Meldung: ${error.message?.slice(0, 300) || "unbekannt"}`,
    `Digest: ${error.digest ?? "-"}`,
    `Browser: ${typeof navigator !== "undefined" ? navigator.userAgent.slice(0, 120) : "?"}`,
    "",
    "Was haben Sie gerade gemacht? (bitte kurz beschreiben)",
  ].join("\n");

  const mailto = `mailto:beamswiss@gmail.com?subject=${encodeURIComponent(
    "Fehlerbericht AI Command Center",
  )}&body=${encodeURIComponent(bericht)}`;

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[#faf8f3] px-6 text-center text-[#241f17]">
      <span className="mb-6 inline-block h-11 w-11 rounded-2xl bg-gradient-to-br from-[#ffb066] to-[#ff5f1f] shadow-[0_8px_30px_rgba(255,120,40,0.35)]" />
      <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
        Da ist etwas schiefgelaufen.
      </h1>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-[#6f6557]">
        Ihre Arbeit ist nicht verloren – Verlauf und Ergebnisse bleiben in
        Ihrem Browser gespeichert. Versuchen Sie es erneut, oder melden Sie
        den Fehler mit einem Klick: Der Bericht enthält alle technischen
        Details, damit wir ihn rasch beheben können.
      </p>
      <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={reset}
          className="shop-btn rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-6 py-3 text-sm font-bold text-white"
        >
          Erneut versuchen
        </button>
        <a
          href={mailto}
          className="shop-btn rounded-xl border border-[#e0d8c6] bg-white px-6 py-3 text-sm font-semibold text-[#6f6557] hover:border-[#ffb066] hover:text-[#c25e0e]"
        >
          Fehler melden
        </a>
      </div>
      {error.digest && (
        <p className="mt-6 font-mono text-[11px] text-[#b3a894]">Fehler-Kennung: {error.digest}</p>
      )}
    </div>
  );
}
