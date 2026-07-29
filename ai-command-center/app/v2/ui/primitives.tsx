/**
 * UI-Primitive (Phase 7) — ausschliesslich token-basiert (var(--…)), keine
 * Hex-Werte. Präsentational, ohne Hooks (server- oder clientseitig nutzbar).
 * Glassmorphism dezent (nur zur Ebenentrennung), Motion 120–200 ms.
 */

import type { CSSProperties, ReactNode } from "react";

export function Surface({ children, style, elevated }: { children: ReactNode; style?: CSSProperties; elevated?: boolean }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        boxShadow: elevated ? "var(--shadow-2)" : "var(--shadow-1)",
        padding: "var(--space-5)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function Button({
  children,
  variant = "primary",
  onClick,
  type = "button",
}: {
  children: ReactNode;
  variant?: "primary" | "ghost";
  onClick?: () => void;
  type?: "button" | "submit";
}) {
  const base: CSSProperties = {
    padding: "var(--space-3) var(--space-5)",
    borderRadius: "var(--radius-full)",
    fontWeight: "var(--weight-medium)" as unknown as number,
    fontSize: "var(--text-sm)",
    cursor: "pointer",
    transition: "filter var(--motion-fast) var(--ease), border-color var(--motion-fast) var(--ease)",
    border: "1px solid transparent",
  };
  const variants: Record<string, CSSProperties> = {
    primary: {
      color: "var(--on-accent)",
      background: "linear-gradient(100deg, var(--accent), var(--accent-2))",
    },
    ghost: {
      color: "var(--text)",
      background: "transparent",
      borderColor: "var(--border)",
    },
  };
  return (
    <button type={type} onClick={onClick} style={{ ...base, ...variants[variant] }}>
      {children}
    </button>
  );
}

export function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Surface style={{ padding: "var(--space-4)" }}>
      <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </div>
      <div style={{ fontSize: "var(--text-2xl)", fontWeight: "var(--weight-bold)" as unknown as number, lineHeight: "var(--leading-tight)", marginTop: "var(--space-2)" }}>
        {value}
      </div>
      {hint ? <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", marginTop: "var(--space-1)" }}>{hint}</div> : null}
    </Surface>
  );
}

export function Badge({ children, tone = "muted" }: { children: ReactNode; tone?: "muted" | "success" | "warning" | "danger" }) {
  const color: Record<string, string> = {
    muted: "var(--text-muted)",
    success: "var(--success)",
    warning: "var(--warning)",
    danger: "var(--danger)",
  };
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-1)",
        fontSize: "var(--text-xs)",
        fontWeight: "var(--weight-medium)" as unknown as number,
        color: color[tone],
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-full)",
        padding: "var(--space-1) var(--space-3)",
      }}
    >
      {children}
    </span>
  );
}
