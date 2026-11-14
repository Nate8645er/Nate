import { motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import type { AppState, ScannerToken, Station } from "../lib/types";

export function Panel({
  title,
  children,
  right,
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
}) {
  return (
    <section className="min-w-0">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[.2em] text-white/45">
          <span className="h-1.5 w-1.5 rounded-sm bg-neon shadow-neon" />
          {title}
        </h2>
        {right}
      </div>
      <div className="rounded-2xl border border-line bg-panel/60 p-4 backdrop-blur-xl min-w-0">
        {children}
      </div>
    </section>
  );
}

export function Row({
  k,
  v,
  tone,
}: {
  k: string;
  v: string;
  tone?: "good" | "bad" | "warn";
}) {
  const color =
    tone === "good"
      ? "text-emerald-400"
      : tone === "bad"
        ? "text-red-400"
        : tone === "warn"
          ? "text-amber-300"
          : "text-white/80";
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line py-2 text-sm last:border-0">
      <span className="text-white/55">{k}</span>
      <span className={`font-mono tabular-nums ${color}`}>{v}</span>
    </div>
  );
}

export function RiskCenter({ state }: { state: AppState }) {
  const L = state.limits;
  const S = state.status as Record<string, string | boolean>;
  const confirmed = Boolean(L.confirmed);
  const stop = state.emergency_stop;
  return (
    <div>
      <Row
        k="Autonomous Live"
        v={S.autonomous_live_locked === false ? "SCHARF" : "LOCKED"}
        tone="bad"
      />
      <Row
        k="Risikolimits bestätigt"
        v={confirmed ? "ja (Nate, 13.11.)" : "nein"}
        tone={confirmed ? "good" : "warn"}
      />
      <Row k="Gesamtkapital" v={`${L.total_capital_usdc} USDC`} />
      <Row
        k="Tagesverlust / Grenze"
        v={`${S.daily_loss_usdc ?? "0"} / ${L.max_daily_loss_usdc} USDC`}
      />
      <Row
        k="Gesamtverlust / Grenze"
        v={`${S.total_loss_usdc ?? "0"} / ${L.max_total_loss_usdc} USDC`}
      />
      <Row k="Max. Slippage" v={`${L.max_slippage_pct} %`} />
      <Row k="Max. offene Exposition" v={`${L.max_open_exposure_usdc} USDC`} />
      <Row k="Hebel / Margin / Transfers" v="deaktiviert" tone="good" />
      <Row
        k="Not-Aus"
        v={stop ? `AKTIV — ${S.emergency_stop_reason ?? ""}` : "bereit"}
        tone={stop ? "bad" : "good"}
      />
      <Row
        k="Not-Aus übersteht Neustart"
        v={S.emergency_stop_persistent ? "ja" : "nein"}
        tone={S.emergency_stop_persistent ? "good" : "bad"}
      />
      <p className="mt-3 flex gap-2 rounded-lg border border-amber-400/30 bg-amber-400/10 p-2 text-[11px] text-amber-200">
        <ShieldAlert size={14} className="mt-px shrink-0" />
        Tages- und Gesamtverlustgrenze entsprechen dem gesamten Kapital. Diese
        Konfiguration erlaubt den Totalverlust der {String(L.total_capital_usdc)} USDC.
      </p>
    </div>
  );
}

export function ConnectorStatus({ stations }: { stations: Station[] }) {
  const connected = stations.filter((s) => s.connected).length;
  return (
    <div>
      <Row
        k="Arbeitsplätze mit Backend"
        v={`${connected} / ${stations.length}`}
        tone={connected === stations.length ? "good" : "warn"}
      />
      {stations.map((s) => (
        <div
          key={s.id}
          className="flex items-center justify-between gap-3 border-b border-line py-2 text-sm last:border-0"
        >
          <span className="flex min-w-0 items-center gap-2">
            <span
              className="h-2 w-2 shrink-0 rounded-sm"
              style={{ background: s.color }}
            />
            <span className="truncate text-white/75">
              {String(s.num).padStart(2, "0")} {s.name}
            </span>
          </span>
          {s.connected ? (
            <span className="flex shrink-0 items-center gap-1 font-mono text-[10px] text-emerald-400">
              <CheckCircle2 size={12} />
              CONNECTED
            </span>
          ) : (
            <span className="flex shrink-0 items-center gap-1 font-mono text-[10px] text-red-400">
              <XCircle size={12} />
              NOT CONNECTED
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

const CATS = [
  { id: "all", label: "Alle" },
  { id: "u100k", label: "< 100k" },
  { id: "u500k", label: "< 500k" },
  { id: "u1m", label: "< 1 Mio." },
  { id: "o1m", label: "> 1 Mio." },
];

const SLURS = [/nigg|n1gg/i, /fa?gg/i];
function mask(name: string) {
  if (!SLURS.some((r) => r.test(name))) return name;
  return name.replace(/[A-Za-z0-9$]+/g, (w) =>
    SLURS.some((r) => r.test(w)) ? w[0] + "•••" : w,
  );
}

export function MarketScanner({
  tokens,
  available,
  reason,
  filter,
  setFilter,
}: {
  tokens: ScannerToken[];
  available: boolean;
  reason?: string;
  filter: string;
  setFilter: (f: string) => void;
}) {
  const match = (t: ScannerToken) => {
    const v = t.mc_or_fdv ?? -1;
    if (filter === "u100k") return v >= 0 && v < 100_000;
    if (filter === "u500k") return v >= 0 && v < 500_000;
    if (filter === "u1m") return v >= 0 && v < 1_000_000;
    if (filter === "o1m") return v >= 1_000_000;
    return true;
  };
  const rows = tokens.filter(match);
  if (!available) {
    return (
      <p className="text-xs text-white/50">
        {reason ?? "Kein Scanner-Snapshot vorhanden."} Es werden keine Token
        erfunden.
      </p>
    );
  }
  return (
    <div className="min-w-0">
      <div className="mb-3 flex flex-wrap gap-2">
        {CATS.map((c) => (
          <button
            key={c.id}
            onClick={() => setFilter(c.id)}
            aria-pressed={filter === c.id}
            className={`rounded-full border px-3 py-1 font-mono text-[10px] tracking-wider ${
              filter === c.id
                ? "border-neon bg-neon text-void"
                : "border-line bg-panel text-white/55"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full text-left text-xs">
          <thead className="bg-black/40 font-mono text-[10px] uppercase tracking-wider text-white/45">
            <tr>
              <th className="p-2">Token</th>
              <th className="p-2">MC/FDV</th>
              <th className="p-2">Liquidität</th>
              <th className="p-2">Vol 24h</th>
              <th className="p-2">Risiko</th>
              <th className="p-2">Veto</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.address} className="border-t border-line">
                <td className="whitespace-nowrap p-2 text-white/80">
                  {mask(t.name)}
                </td>
                <td className="whitespace-nowrap p-2 font-mono tabular-nums">
                  {t.mc_or_fdv == null
                    ? "UNKNOWN"
                    : `$${Math.round(t.mc_or_fdv).toLocaleString()}`}
                  {t.uncertain && <span className="text-white/35"> ?</span>}
                </td>
                <td className="whitespace-nowrap p-2 font-mono tabular-nums">
                  {t.liquidity_usd == null
                    ? "UNKNOWN"
                    : `$${Math.round(t.liquidity_usd).toLocaleString()}`}
                </td>
                <td className="whitespace-nowrap p-2 font-mono tabular-nums">
                  {t.volume_24h == null
                    ? "UNKNOWN"
                    : `$${Math.round(t.volume_24h).toLocaleString()}`}
                </td>
                <td className="whitespace-nowrap p-2">
                  <span
                    className={`font-mono text-[10px] ${
                      t.risk === "CRITICAL" || t.risk === "HIGH"
                        ? "text-red-400"
                        : t.risk === "UNKNOWN"
                          ? "text-white/50"
                          : "text-emerald-400"
                    }`}
                  >
                    {t.risk}
                  </span>
                </td>
                <td className="whitespace-nowrap p-2">
                  {t.veto ? (
                    <span className="flex items-center gap-1 font-mono text-[10px] text-red-400">
                      <AlertTriangle size={11} />
                      NO TRADE
                    </span>
                  ) : (
                    <span className="font-mono text-[10px] text-white/45">
                      —
                    </span>
                  )}
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="p-3 text-center text-white/40">
                  Kein Token in diesem Filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[11px] text-white/40">
        Quellen: GeckoTerminal, DexScreener, Solana RPC. Fehlende Werte zeigen
        UNKNOWN. Niedrige Market Cap ist kein Kaufsignal.
      </p>
    </div>
  );
}

export function ModeBadge({ mode, stop }: { mode: string; stop: boolean }) {
  const tone = stop
    ? "border-loss/60 text-loss bg-loss/10"
    : mode === "PAPER"
      ? "border-amber-400/50 text-amber-300 bg-amber-400/10"
      : "border-emerald-400/50 text-emerald-300 bg-emerald-400/10";
  return (
    <motion.span
      layout
      className={`rounded-full border px-3 py-1 font-mono text-[10px] tracking-widest ${tone}`}
    >
      {stop ? "NOT-AUS" : mode}
    </motion.span>
  );
}
