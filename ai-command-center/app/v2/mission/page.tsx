"use client";

/**
 * /v2/mission (Vorschau) — Missions-Eingabe mit LIVE-Routing-Anzeige aus dem
 * platform-backend: „Wo läuft das?" (Lokal im Haus ↔ Cloud) inkl. Begründung,
 * abhängig von der gewählten Datenklasse. Ist kein Backend verbunden, zeigt die
 * Karte ehrlich „—" statt eines erfundenen Status. Token-only, theme-aware.
 */

import { useEffect, useState } from "react";
import { Badge, Button, Surface } from "../ui/primitives";

type DataClass = "internal" | "local_only" | "public";

interface Decision {
  placement: "local" | "cloud";
  reason: string;
  fallback: "local" | "cloud" | null;
}

export default function V2MissionPage() {
  const [goal, setGoal] = useState("");
  const [dataClass, setDataClass] = useState<DataClass>("internal");
  const [connected, setConnected] = useState<boolean | null>(null);
  const [decision, setDecision] = useState<Decision | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      try {
        const res = await fetch("/api/platform/route", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ goal, dataClass }),
          signal: ctrl.signal,
        });
        const data = (await res.json()) as { connected: boolean; decision?: Decision };
        setConnected(data.connected);
        setDecision(data.decision ?? null);
      } catch {
        /* Abbruch/Netz — Anzeige bleibt unverändert */
      }
    }, 300);
    return () => {
      clearTimeout(t);
      ctrl.abort();
    };
  }, [goal, dataClass]);

  const wo = !connected || !decision ? "—" : decision.placement === "local" ? "Lokal (im Haus)" : "Cloud";
  const hint = connected === null ? "prüfe Verbindung …" : !connected ? "Backend nicht verbunden" : decision?.reason ?? "";

  return (
    <main style={{ maxWidth: 900, margin: "0 auto", padding: "var(--space-6) var(--space-5)" }}>
      <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.2em" }}>
        AI Command Center
      </div>
      <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 800, lineHeight: "var(--leading-tight)", margin: "var(--space-2) 0 var(--space-5)" }}>
        Neue Mission
      </h1>

      <Surface elevated>
        <label htmlFor="goal" style={{ fontWeight: 600, fontSize: "var(--text-sm)" }}>Auftrag</label>
        <textarea
          id="goal"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="z. B. „Erstelle eine Offerte für eine Badezimmer-Renovation …"
          rows={4}
          style={{
            width: "100%",
            marginTop: "var(--space-2)",
            padding: "var(--space-3)",
            borderRadius: "var(--radius-md)",
            border: "1px solid var(--border)",
            background: "var(--surface-2)",
            color: "var(--text)",
            fontSize: "var(--text-sm)",
            fontFamily: "inherit",
            resize: "vertical",
          }}
        />

        <div style={{ marginTop: "var(--space-4)", display: "flex", gap: "var(--space-2)", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>Datenklasse:</span>
          {(["internal", "local_only", "public"] as DataClass[]).map((dc) => (
            <Button key={dc} variant={dataClass === dc ? "primary" : "ghost"} onClick={() => setDataClass(dc)}>
              {dc === "internal" ? "Intern" : dc === "local_only" ? "Nur lokal" : "Öffentlich"}
            </Button>
          ))}
        </div>
      </Surface>

      {/* Live-Routing-Anzeige aus dem Backend */}
      <Surface style={{ marginTop: "var(--space-4)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-3)", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Wo läuft das?
            </div>
            <div style={{ fontSize: "var(--text-xl)", fontWeight: 800, marginTop: "var(--space-1)" }}>{wo}</div>
            <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>{hint}</div>
          </div>
          <Badge tone={connected ? "success" : "muted"}>
            {connected === null ? "…" : connected ? "Backend verbunden" : "Demo (kein Backend)"}
          </Badge>
        </div>
        {decision?.fallback ? (
          <div style={{ marginTop: "var(--space-3)", fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>
            Ausweich-Route: {decision.fallback === "local" ? "Lokal" : "Cloud"}
          </div>
        ) : null}
      </Surface>

      <div style={{ marginTop: "var(--space-5)", display: "flex", gap: "var(--space-2)" }}>
        <Button>Mission starten</Button>
        <Button variant="ghost" onClick={() => setGoal("")}>Zurücksetzen</Button>
      </div>
    </main>
  );
}
