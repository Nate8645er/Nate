import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./ui-tokens.css";
import { flagFromEnv } from "@/lib/flags";

export const metadata: Metadata = {
  title: "AI Command Center — v2 (Vorschau)",
};

/**
 * Layout des neuen Premium-UI (Phase 7). Additiv: eigener Token-Scope `.v2`,
 * eigenes Stylesheet – das bestehende UI unter anderen Routen bleibt unberührt.
 * Ohne Feature-Flag erscheint ein ehrlicher Vorschau-Hinweis.
 */
const NAV = [
  { href: "/v2", label: "Dashboard" },
  { href: "/v2/mission", label: "Neue Mission" },
  { href: "/v2/enterprise", label: "Enterprise" },
];

export default function V2Layout({ children }: { children: ReactNode }) {
  const aktiv = flagFromEnv("ui_v2");
  return (
    <div className="v2" style={{ minHeight: "100dvh" }}>
      {!aktiv ? (
        <div
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--text-muted)",
            textAlign: "center",
            padding: "var(--space-2)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          Vorschau des neuen Designs · produktiv per <code>NEXT_PUBLIC_UI_V2=1</code> schalten
        </div>
      ) : null}
      <nav
        style={{
          display: "flex",
          gap: "var(--space-4)",
          alignItems: "center",
          padding: "var(--space-3) var(--space-5)",
          borderBottom: "1px solid var(--border)",
          maxWidth: 1160,
          margin: "0 auto",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontWeight: 800, fontSize: "var(--text-sm)", letterSpacing: "0.02em" }}>ACC</span>
        {NAV.map((n) => (
          <a
            key={n.href}
            href={n.href}
            style={{ color: "var(--text-muted)", textDecoration: "none", fontSize: "var(--text-sm)", fontWeight: 600 }}
          >
            {n.label}
          </a>
        ))}
      </nav>
      {children}
    </div>
  );
}
