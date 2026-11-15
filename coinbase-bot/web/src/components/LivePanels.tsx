import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, RefreshCw, ShieldAlert, XCircle } from "lucide-react";
import { api, getRole } from "../lib/api";
import type { LiveOverview, Readiness } from "../lib/types";
import { Row } from "./Panels";

const usdc = (v: string | number | null | undefined) =>
  v === null || v === undefined ? "UNBEKANNT" : `${Number(v).toFixed(4)} USDC`;

const tone = (v: string | null | undefined) =>
  v === null || v === undefined || Number(v) === 0
    ? undefined
    : Number(v) > 0
      ? ("good" as const)
      : ("bad" as const);

/** Real-money figures only. Null from the backend is shown as UNBEKANNT. */
export function LiveProfitPanel({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<LiveOverview | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api
      .live()
      .then((d) => {
        setData(d);
        setError("");
      })
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  useEffect(load, [load, refreshKey]);

  if (error)
    return (
      <p className="text-sm text-red-400">Live-Daten nicht lesbar: {error}</p>
    );
  if (!data) return <p className="text-sm text-white/45">Lade echte Werte …</p>;

  return (
    <div>
      <div
        className={`mb-3 inline-flex items-center gap-2 rounded-md border px-2 py-1 font-mono text-[11px] ${
          data.is_live
            ? "border-red-400/50 bg-red-400/10 text-red-300"
            : "border-line bg-white/5 text-white/60"
        }`}
      >
        {data.is_live
          ? "LIVE — ECHTGELD"
          : "PAPER — es wird kein echtes Geld bewegt"}
      </div>
      <Row k="Real Balance / Available USDC" v={usdc(data.real_balance_usdc)} />
      <Row k="Quelle" v={data.balance_source} />
      <Row k="Allocated Capital" v={usdc(data.allocated_capital_usdc)} />
      <Row k="Open Positions" v={String(data.open_positions.length)} />
      <Row
        k="Realized P&L"
        v={usdc(data.realised_pnl_usdc)}
        tone={tone(data.realised_pnl_usdc)}
      />
      <Row
        k="Unrealized P&L"
        v={usdc(data.unrealised_pnl_usdc)}
        tone={tone(data.unrealised_pnl_usdc)}
      />
      <Row
        k="Daily P&L"
        v={usdc(data.daily_pnl_usdc)}
        tone={tone(data.daily_pnl_usdc)}
      />
      <Row
        k="Total P&L"
        v={usdc(data.total_pnl_usdc)}
        tone={tone(data.total_pnl_usdc)}
      />
      <Row k="Trading Fees" v={usdc(data.trading_fees_usdc)} />
      {data.open_positions.map((p) => (
        <Row
          key={p.product_id}
          k={`${p.product_id}${p.partial ? " (Teil-Fill)" : ""}`}
          v={`${p.base_size} · Kosten ${Number(p.cost_usdc).toFixed(4)}`}
        />
      ))}
      <p className="mt-3 text-[11px] text-white/45">{data.note}</p>
    </div>
  );
}

export function OrderHistoryPanel({ refreshKey }: { refreshKey: number }) {
  const [data, setData] = useState<LiveOverview | null>(null);
  useEffect(() => {
    api
      .live()
      .then(setData)
      .catch(() => setData(null));
  }, [refreshKey]);
  const rows = data?.order_history ?? [];
  return (
    <div>
      <Row k="Echte Orders dieses Systems" v={String(rows.length)} />
      {rows.map((o) => (
        <Row
          key={o.client_order_id}
          k={`${o.side ?? o.outcome?.side ?? "?"} ${o.product_id ?? ""}`}
          v={o.outcome?.state ?? "UNGEKLÄRT"}
          tone={
            o.outcome?.state === "FILLED" ? "good" : o.outcome ? "warn" : "bad"
          }
        />
      ))}
      <p className="mt-2 text-[11px] text-white/45">
        Der verifizierte Echtgeld-Round-Trip vom 13.11. (Kauf und Verkauf
        BTC-USDC, Ergebnis −0.0233 USDC inkl. Gebühren) ist in
        docs/AUDIT_2026-11-13_coinbase_live_roundtrip.md dokumentiert.
      </p>
    </div>
  );
}

/** LIVE_READINESS_CHECK. Runs on demand, shows all 14 criteria, arms nothing. */
export function ReadinessPanel() {
  const [report, setReport] = useState<Readiness | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const admin = getRole() === "admin";

  const run = async () => {
    setBusy(true);
    setError("");
    try {
      setReport(await api.readiness());
    } catch (e: any) {
      setError(
        e.message === "FORBIDDEN" ? "Nur für Admins." : String(e.message ?? e),
      );
    } finally {
      setBusy(false);
    }
  };

  const ready = report?.verdict.startsWith("READY");
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <span
          className={`rounded-md border px-2 py-1 font-mono text-[11px] ${
            !report
              ? "border-line text-white/50"
              : ready
                ? "border-emerald-400/50 bg-emerald-400/10 text-emerald-300"
                : "border-red-400/50 bg-red-400/10 text-red-300"
          }`}
        >
          {report
            ? `${report.verdict} · ${report.passed}/${report.total}`
            : "noch nicht geprüft"}
        </span>
        <button
          onClick={run}
          disabled={busy || !admin}
          className="inline-flex min-h-[40px] items-center gap-2 rounded-lg border border-line bg-white/5 px-3 text-xs text-white/80 disabled:opacity-40"
        >
          <RefreshCw size={14} className={busy ? "animate-spin" : ""} />
          Prüfung starten
        </button>
      </div>
      {error && <p className="mb-2 text-sm text-red-400">{error}</p>}
      {report?.criteria.map((c) => (
        <details
          key={c.key}
          className="border-b border-line py-2 last:border-0"
        >
          <summary className="flex cursor-pointer list-none items-center gap-2 text-sm">
            {c.passed ? (
              <CheckCircle2 size={15} className="shrink-0 text-emerald-400" />
            ) : (
              <XCircle size={15} className="shrink-0 text-red-400" />
            )}
            <span className="text-white/80">
              {c.number}. {c.title}
            </span>
          </summary>
          <ul className="mt-1 space-y-0.5 pl-6 font-mono text-[11px] text-white/50">
            {c.evidence.map((line, i) => (
              <li key={i} className="break-words">
                {line}
              </li>
            ))}
          </ul>
        </details>
      ))}
      {report && (
        <p className="mt-3 flex gap-2 rounded-lg border border-amber-400/30 bg-amber-400/10 p-2 text-[11px] text-amber-200">
          <ShieldAlert size={14} className="mt-px shrink-0" />
          Autonomous Live: {report.live_autonomous_enabled
            ? "SCHARF"
            : "AUS"}. {report.note}
          {report.connector_note ? ` Connector: ${report.connector_note}.` : ""}
        </p>
      )}
    </div>
  );
}
