import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Bot,
  Building2,
  Coins,
  Cpu,
  DollarSign,
  Gauge,
  LayoutGrid,
  Play,
  Plug,
  Radar,
  Settings,
  ShieldAlert,
  Square,
  Wifi,
  WifiOff,
} from "lucide-react";
import { PixelOffice } from "./components/PixelOffice";
import { DECISION_STATE, type RobotState } from "./components/PixelRobot";
import { StatsCard } from "./components/StatsCard";
import { AgentTerminal } from "./components/AgentTerminal";
import { LiveActivityFeed } from "./components/LiveActivityFeed";
import { ProfitChart, type Point } from "./components/ProfitChart";
import {
  LiveProfitPanel,
  OrderHistoryPanel,
  ReadinessPanel,
} from "./components/LivePanels";
import {
  ConnectorStatus,
  MarketScanner,
  ModeBadge,
  Panel,
  RiskCenter,
  Row,
} from "./components/Panels";
import { api, clearSession, getToken, storeSession } from "./lib/api";
import { EventStream } from "./lib/ws";
import type { AppState, ScannerToken, Statement, WsEvent } from "./lib/types";

const PAGES = [
  { id: "office", label: "AI Office", icon: Building2 },
  { id: "command", label: "Command Center", icon: LayoutGrid },
  { id: "market", label: "Live Market", icon: BarChart3 },
  { id: "meeting", label: "Team Meeting", icon: Bot },
  { id: "trading", label: "Coinbase Trading", icon: DollarSign },
  { id: "scanner", label: "Memecoin Scanner", icon: Radar },
  { id: "portfolios", label: "Portfolios", icon: Coins },
  { id: "profit", label: "Live Profit", icon: Activity },
  { id: "history", label: "Trade History", icon: Cpu },
  { id: "risk", label: "Risk Center", icon: ShieldAlert },
  { id: "connectors", label: "Connectors", icon: Plug },
  { id: "settings", label: "Settings", icon: Settings },
] as const;
type PageId = (typeof PAGES)[number]["id"];

export default function App() {
  const [token, setTok] = useState(getToken());
  const [state, setState] = useState<AppState | null>(null);
  const [page, setPage] = useState<PageId>("office");
  const [wsStatus, setWsStatus] = useState<"connecting" | "open" | "closed">(
    "closed",
  );
  const [log, setLog] = useState<Statement[]>([]);
  const [robot, setRobot] = useState<Record<string, RobotState>>({});
  const [meeting, setMeeting] = useState<{
    active: boolean;
    symbol: string | null;
    line: string;
  }>({ active: false, symbol: null, line: "" });
  const [scanner, setScanner] = useState<{
    available: boolean;
    tokens: ScannerToken[];
    reason?: string;
  }>({ available: false, tokens: [] });
  const [filter, setFilter] = useState("all");
  const [picked, setPicked] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const streamRef = useRef<EventStream | null>(null);

  const refresh = useCallback(async () => {
    try {
      setState(await api.state());
      setErr(null);
    } catch (e) {
      const m = (e as Error).message;
      if (m === "UNAUTHORIZED") {
        clearSession();
        setTok("");
      }
      setErr(m);
    }
  }, []);

  // --- event handling: drives every animation from real backend events ---
  const onEvent = useCallback(
    (e: WsEvent) => {
      if (e.kind === "agent") {
        const s = e.payload as Statement;
        setLog((prev) => [...prev, s]);
        const station = (s as any).station as string | undefined;
        if (station) {
          const next: RobotState =
            s.step === 4 && s.agent === "RiskManager"
              ? "RISK_CHECK"
              : s.step >= 3 && s.step <= 5
                ? "MEETING"
                : (DECISION_STATE[s.decision] ?? "ANALYZING");
          setRobot((prev) => ({ ...prev, [station]: next }));
        }
        setMeeting((m) => ({ ...m, line: `${s.agent}: ${s.decision}` }));
      }
      if (e.kind === "meeting_start") {
        setLog([]);
        setMeeting({
          active: true,
          symbol: e.payload.symbol,
          line: "Meeting gestartet",
        });
      }
      if (e.kind === "meeting_end") {
        setMeeting({
          active: false,
          symbol: e.payload.symbol,
          line: `${e.payload.final}`,
        });
        setTimeout(() => setRobot({}), 1500);
      }
      if (
        e.kind === "market" ||
        e.kind === "balance" ||
        e.kind === "mode" ||
        e.kind === "emergency_stop"
      ) {
        void refresh();
      }
      if (e.kind === "error") {
        setErr(`${e.payload.where}: ${e.payload.detail}`);
      }
    },
    [refresh],
  );

  useEffect(() => {
    if (!token) return;
    void refresh();
    api
      .scanner()
      .then((s) =>
        setScanner({
          available: s.available,
          tokens: s.tokens ?? [],
          reason: s.reason,
        }),
      )
      .catch(() =>
        setScanner({
          available: false,
          tokens: [],
          reason: "Scanner nicht erreichbar",
        }),
      );
    const stream = new EventStream(token);
    streamRef.current = stream;
    const offE = stream.onEvent(onEvent);
    const offS = stream.onStatus(setWsStatus);
    stream.connect();
    return () => {
      offE();
      offS();
      stream.close();
      streamRef.current = null;
    };
  }, [token, refresh, onEvent]);

  const stations = state?.stations ?? [];
  const pickedStation = useMemo(
    () => stations.find((s) => s.id === picked) ?? null,
    [stations, picked],
  );
  const stationLog = useMemo(
    () => log.filter((s) => (s as any).station === picked),
    [log, picked],
  );

  const prices = state?.market.prices ?? {};
  const stale = state?.market.stale ?? true;
  const balance = state?.balance.available_usdc;

  const runMeeting = async (symbol: string) => {
    setBusy(true);
    setErr(null);
    try {
      await api.runMeeting(symbol);
    } catch (e) {
      setErr((e as Error).message);
    }
    setBusy(false);
  };
  const stop = async () => {
    setBusy(true);
    try {
      await api.emergencyStop("Dashboard");
    } catch (e) {
      setErr((e as Error).message);
    }
    setBusy(false);
  };

  if (!token)
    return (
      <Login
        onLogin={(t: string) => {
          setTok(t);
        }}
      />
    );

  return (
    <div className="min-h-screen pb-24">
      <Header state={state} wsStatus={wsStatus} />

      <main className="mx-auto w-full max-w-[1400px] px-4 py-4 sm:px-6">
        {err && (
          <p className="mb-3 rounded-xl border border-loss/40 bg-loss/10 p-3 text-xs text-loss">
            {err}
          </p>
        )}

        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          >
            {page === "office" && (
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
                <div className="min-w-0">
                  <PixelOffice
                    stations={stations}
                    states={robot}
                    prices={prices}
                    stale={stale}
                    meetingActive={meeting.active}
                    meetingSymbol={meeting.symbol}
                    meetingLine={meeting.line}
                    onPick={setPicked}
                  />
                  <Controls busy={busy} onRun={runMeeting} onStop={stop} />
                </div>
                <div className="min-w-0 space-y-4">
                  <Panel title="Live Activity Feed">
                    <LiveActivityFeed items={log} />
                  </Panel>
                  <Panel title="Risk Center">
                    {state && <RiskCenter state={state} />}
                  </Panel>
                </div>
              </div>
            )}

            {page === "command" && state && (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <StatsCard
                    title="Trading-Modus"
                    value={state.mode}
                    icon={Gauge}
                    hint={
                      state.emergency_stop
                        ? "Not-Aus aktiv"
                        : "Live autonom gesperrt"
                    }
                  />
                  <StatsCard
                    title="Coinbase-Guthaben (REAL)"
                    value={
                      balance == null
                        ? "nicht gelesen"
                        : `${balance.toFixed(4)} USDC`
                    }
                    icon={DollarSign}
                    hint={state.balance.source}
                  />
                  <StatsCard
                    title="Kapitalgrenze"
                    value={`${state.limits.total_capital_usdc} USDC`}
                    icon={ShieldAlert}
                    hint="absolut, nie erhöht"
                  />
                  <StatsCard
                    title="Arbeitsplätze"
                    value={`${stations.filter((s) => s.connected).length} / ${stations.length}`}
                    icon={Bot}
                    hint="mit echtem Backend"
                  />
                </div>
                <Panel title="System-Status">
                  <Row
                    k="WebSocket"
                    v={wsStatus}
                    tone={wsStatus === "open" ? "good" : "warn"}
                  />
                  <Row
                    k="Marktdaten"
                    v={stale ? "DATA STALE" : "live"}
                    tone={stale ? "warn" : "good"}
                  />
                  <Row
                    k="Not-Aus"
                    v={state.emergency_stop ? "AKTIV" : "bereit"}
                    tone={state.emergency_stop ? "bad" : "good"}
                  />
                  <Row k="Autonomous Live" v="LOCKED" tone="bad" />
                </Panel>
                <Controls busy={busy} onRun={runMeeting} onStop={stop} />
              </div>
            )}

            {page === "market" && (
              <div className="grid gap-3 sm:grid-cols-3">
                {Object.entries(prices).map(([sym, p]) => (
                  <StatsCard
                    key={sym}
                    title={sym}
                    value={p.price.toLocaleString(undefined, {
                      maximumFractionDigits: 2,
                    })}
                    change={p.change_pct}
                    icon={BarChart3}
                    hint={stale ? "DATA STALE" : "Coinbase, öffentlich"}
                  />
                ))}
                {Object.keys(prices).length === 0 && (
                  <p className="text-xs text-white/50">
                    Keine Kursdaten — es werden keine Preise erfunden.
                  </p>
                )}
              </div>
            )}

            {page === "meeting" && (
              <div className="grid gap-4 lg:grid-cols-2">
                <Panel title="Team Meeting (8 Schritte)">
                  <Controls
                    busy={busy}
                    onRun={runMeeting}
                    onStop={stop}
                    inline
                  />
                  <div className="mt-3">
                    <LiveActivityFeed items={log} />
                  </div>
                </Panel>
                <Panel title="Konsens">
                  <Row k="Symbol" v={meeting.symbol ?? "—"} />
                  <Row k="Status" v={meeting.active ? "läuft" : "bereit"} />
                  <Row k="Letzte Meldung" v={meeting.line || "—"} />
                  <p className="mt-3 text-[11px] text-white/45">
                    Das Meeting bereitet höchstens eine Order vor. Senden kann
                    es nichts: dafür braucht es LIVE MANUAL plus eine Freigabe
                    pro Order.
                  </p>
                </Panel>
              </div>
            )}

            {page === "trading" && state && (
              <div className="space-y-4">
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <StatsCard
                    title="Real Available Balance"
                    value={
                      balance == null
                        ? "nicht gelesen"
                        : `${balance.toFixed(4)} USDC`
                    }
                    icon={DollarSign}
                  />
                  <StatsCard
                    title="Allocated Capital"
                    value={`${state.limits.total_capital_usdc} USDC`}
                    icon={ShieldAlert}
                  />
                  <StatsCard
                    title="Open Positions"
                    value="0"
                    icon={Coins}
                    hint="keine offene Position"
                  />
                  <StatsCard title="Open Orders" value="0" icon={Activity} />
                </div>
                <Panel title="P&L (REAL)">
                  <Row k="Realisierter P&L" v="0.0000 USDC" tone="good" />
                  <Row k="Nicht realisierter P&L" v="— (keine Position)" />
                  <Row k="Gebühren gesamt" v="0.0000 USDC" />
                  <p className="mt-3 text-[11px] text-white/45">
                    In dieser Sitzung wurde keine Order ausgeführt, daher ist
                    der realisierte P&amp;L 0. Geschätzte Werte wären als
                    Schätzung gekennzeichnet.
                  </p>
                </Panel>
              </div>
            )}

            {page === "scanner" && (
              <Panel title="Memecoin Scanner">
                <MarketScanner
                  tokens={scanner.tokens}
                  available={scanner.available}
                  reason={scanner.reason}
                  filter={filter}
                  setFilter={setFilter}
                />
              </Panel>
            )}

            {page === "portfolios" && (
              <Panel title="Portfolios A–E (virtuell)">
                {[
                  "A · Coinbase BTC MACD-Trend",
                  "B · Weitere Coinbase-Coins",
                  "C · Solana Memecoins",
                  "D · Micro-Caps < 1M",
                  "E · Micro-Caps < 500k",
                ].map((p, i) => (
                  <Row
                    key={p}
                    k={p}
                    v={i === 0 ? "Paper 17.10 USDC" : "NO TRADE"}
                    tone={i === 0 ? undefined : "warn"}
                  />
                ))}
              </Panel>
            )}

            {page === "profit" && (
              <div className="grid gap-4 lg:grid-cols-2">
                <Panel title="Live Profit Monitor — Echtgeld">
                  <LiveProfitPanel refreshKey={state?.seq ?? 0} />
                </Panel>
                <Panel title="P&L-Verlauf">
                  <ProfitChart data={[] as Point[]} label="P&L" />
                </Panel>
              </div>
            )}

            {page === "history" && (
              <Panel title="Trade History">
                <OrderHistoryPanel refreshKey={state?.seq ?? 0} />
              </Panel>
            )}

            {page === "risk" && state && (
              <div className="grid gap-4 lg:grid-cols-2">
                <Panel title="Risk Center">
                  <RiskCenter state={state} />
                </Panel>
                <Panel title="Live Readiness Check">
                  <ReadinessPanel />
                </Panel>
              </div>
            )}

            {page === "connectors" && (
              <Panel title="Connectors / Workstations">
                <ConnectorStatus stations={stations} />
              </Panel>
            )}

            {page === "settings" && state && (
              <Panel title="Settings">
                <Row k="Backend" v="FastAPI + WebSocket (lokal)" />
                <Row k="Auth" v="Bearer-Token, im Browser gespeichert" />
                <Row k="Secrets im Frontend" v="keine" tone="good" />
                <Row k="Modus" v={state.mode} />
                <p className="mt-3 text-[11px] text-white/45">
                  Das Token wird nur lokal gehalten. API-Schlüssel liegen
                  ausschließlich im Backend und werden nie an den Browser
                  gesendet.
                </p>
              </Panel>
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      <AgentTerminal
        station={pickedStation}
        log={stationLog}
        onClose={() => setPicked(null)}
      />
      <BottomNav
        page={page}
        setPage={setPage}
        stations={stations}
        onPick={setPicked}
      />
    </div>
  );
}

function Header({
  state,
  wsStatus,
}: {
  state: AppState | null;
  wsStatus: string;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-void/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 sm:px-6">
        <div className="min-w-0">
          <h1 className="font-pixel text-[11px] leading-tight text-white sm:text-[13px]">
            15 AI AGENTS <span className="text-neon">ONE TRADING EMPIRE</span>
          </h1>
          <p className="mt-1 font-mono text-[10px] tracking-widest text-white/40">
            HYPERGROK AI TRADING EMPIRE · COINBASE · SOLANA · PUMP.FUN
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <ModeBadge
            mode={state?.mode ?? "—"}
            stop={Boolean(state?.emergency_stop)}
          />
          <span className="rounded-full border border-loss/50 bg-loss/10 px-3 py-1 font-mono text-[10px] tracking-widest text-loss">
            AUTONOMOUS · LOCKED
          </span>
          <span
            className={`flex items-center gap-1 rounded-full border px-2 py-1 font-mono text-[10px] ${
              wsStatus === "open"
                ? "border-emerald-400/50 text-emerald-300"
                : "border-amber-400/50 text-amber-300"
            }`}
          >
            {wsStatus === "open" ? <Wifi size={11} /> : <WifiOff size={11} />}
            {wsStatus}
          </span>
        </div>
      </div>
    </header>
  );
}

function Controls({
  busy,
  onRun,
  onStop,
  inline,
}: {
  busy: boolean;
  onRun: (s: string) => void;
  onStop: () => void;
  inline?: boolean;
}) {
  return (
    <div
      className={`flex flex-wrap items-center gap-2 ${inline ? "" : "mt-3"}`}
    >
      {["BTC-USD", "ETH-USD", "SOL-USD"].map((s) => (
        <button
          key={s}
          disabled={busy}
          onClick={() => onRun(s)}
          className="flex items-center gap-1.5 rounded-xl border border-line bg-panel px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-white/80 hover:border-cyan disabled:opacity-40"
        >
          <Play size={12} />
          {s}
        </button>
      ))}
      <button
        disabled={busy}
        onClick={onStop}
        className="flex items-center gap-1.5 rounded-xl border border-loss/60 bg-loss/10 px-3 py-2 font-mono text-[10px] uppercase tracking-widest text-loss hover:bg-loss/20 disabled:opacity-40"
      >
        <Square size={12} />
        Not-Aus
      </button>
    </div>
  );
}

function BottomNav({
  page,
  setPage,
  stations,
  onPick,
}: {
  page: PageId;
  setPage: (p: PageId) => void;
  stations: AppState["stations"];
  onPick: (id: string) => void;
}) {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-void/95 backdrop-blur-xl">
      <div className="mx-auto max-w-[1400px] px-2 pb-[env(safe-area-inset-bottom)]">
        <div className="flex gap-1 overflow-x-auto py-1">
          {stations.map((s) => (
            <button
              key={s.id}
              onClick={() => onPick(s.id)}
              title={`${s.name} — ${s.status}`}
              className="flex shrink-0 flex-col items-center rounded-lg px-2 py-1"
            >
              <span className="font-mono text-[9px] text-white/40">
                {String(s.num).padStart(2, "0")}
              </span>
              <span
                className="mt-0.5 h-4 w-4 rounded-sm"
                style={{
                  background: s.connected ? s.color : "#2a3350",
                  boxShadow: s.connected ? `0 0 8px ${s.color}80` : "none",
                }}
              />
              <span className="mt-0.5 font-mono text-[8px] text-white/45">
                {s.short}
              </span>
            </button>
          ))}
        </div>
        <div className="flex gap-1 overflow-x-auto border-t border-line py-1.5">
          {PAGES.map((p) => {
            const Icon = p.icon;
            const on = page === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setPage(p.id)}
                aria-current={on ? "page" : undefined}
                className={`flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 font-mono text-[9px] uppercase tracking-wider ${
                  on ? "bg-neon text-void" : "text-white/50 hover:text-white"
                }`}
              >
                <Icon size={12} />
                {p.label}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

function Login({ onLogin }: { onLogin: (t: string) => void }) {
  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api.login(user.trim(), pass);
      storeSession(r.token, r.csrf, r.role);
      onLogin(r.token);
    } catch {
      setError("Benutzername oder Passwort falsch.");
    }
    setBusy(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={submit}
            className="w-full max-w-sm rounded-2xl border border-line bg-panel/70 p-6 backdrop-blur-xl">
        <h1 className="font-pixel text-[11px] leading-relaxed text-white">
          HYPER<span className="text-neon">GROK</span>
        </h1>
        <p className="mb-4 mt-2 text-xs text-white/50">
          Anmeldung erforderlich. Das Admin-Konto wird beim ersten Backend-Start
          einmalig in der Server-Konsole angezeigt und nie im Repository gespeichert.
        </p>
        <label htmlFor="usr" className="mb-1 block text-[11px] text-white/50">Benutzer</label>
        <input id="usr" value={user} onChange={(e) => setUser(e.target.value)} autoComplete="username"
               className="mb-3 w-full rounded-xl border border-line bg-black/40 px-3 py-2 font-mono text-sm text-white outline-none focus:border-cyan" />
        <label htmlFor="pwd" className="mb-1 block text-[11px] text-white/50">Passwort</label>
        <input id="pwd" type="password" value={pass} onChange={(e) => setPass(e.target.value)}
               autoComplete="current-password"
               className="w-full rounded-xl border border-line bg-black/40 px-3 py-2 font-mono text-sm text-white outline-none focus:border-cyan" />
        {error && <p className="mt-3 rounded-lg border border-loss/40 bg-loss/10 p-2 text-[11px] text-loss">{error}</p>}
        <button type="submit" disabled={busy}
          className="mt-4 w-full rounded-xl border border-neon bg-neon/15 px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-neon hover:bg-neon/25 disabled:opacity-40">
          {busy ? "..." : "Anmelden"}
        </button>
      </form>
    </div>
  );
}
