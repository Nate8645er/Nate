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
      {children}
    </div>
  );
}
