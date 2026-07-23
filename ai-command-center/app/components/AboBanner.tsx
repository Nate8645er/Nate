"use client";

/**
 * Schlanker, isolierter Abo-Hinweis für das Dashboard.
 *
 * Fragt GET /api/mein-abo (angemeldete Sitzung → echter Plan aus dem
 * Kunden-Store). Rendert bewusst NICHTS, wenn kein Abo vorliegt, die Route
 * nicht konfiguriert ist oder der/die Nutzer:in nicht angemeldet ist (401) –
 * so bleibt das Dashboard ohne Login unverändert.
 */

import { useEffect, useState } from "react";
import Link from "next/link";

interface Abo {
  planName: string;
  status: string;
  aktiv: boolean;
  lizenzSchluessel: string | null;
}

export default function AboBanner() {
  const [abo, setAbo] = useState<Abo | null>(null);
  const [weg, setWeg] = useState(false);

  useEffect(() => {
    let ok = true;
    (async () => {
      try {
        const res = await fetch("/api/mein-abo");
        if (!res.ok) return; // 401/404/501 → still nichts anzeigen
        const data = (await res.json()) as Abo;
        if (ok && data?.planName) setAbo(data);
      } catch {
        /* offline / nicht angemeldet → nichts anzeigen */
      }
    })();
    return () => {
      ok = false;
    };
  }, []);

  if (!abo || weg) return null;

  return (
    <div
      role="status"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        flexWrap: "wrap",
        margin: "0 0 16px",
        padding: "10px 14px",
        borderRadius: 14,
        border: "1px solid rgba(255,140,42,.35)",
        background: "linear-gradient(90deg,rgba(255,140,42,.10),rgba(236,72,153,.08))",
        fontSize: 14,
      }}
    >
      <span style={{ fontWeight: 700 }}>
        Ihr Abo: {abo.planName}
        <span style={{ fontWeight: 500, opacity: 0.8 }}>
          {" "}· {abo.aktiv ? "aktiv" : abo.status}
        </span>
      </span>
      {abo.lizenzSchluessel && (
        <Link href="/konto" style={{ fontWeight: 700, color: "#c25e0e" }}>
          Lizenzschlüssel im Konto →
        </Link>
      )}
      <button
        type="button"
        onClick={() => setWeg(true)}
        aria-label="Hinweis schliessen"
        style={{
          marginLeft: "auto",
          border: 0,
          background: "transparent",
          cursor: "pointer",
          fontSize: 18,
          lineHeight: 1,
          color: "inherit",
          opacity: 0.6,
        }}
      >
        ×
      </button>
    </div>
  );
}
