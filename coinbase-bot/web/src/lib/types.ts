export type Station = {
  id: string; num: number; name: string; short: string; color: string;
  backend: string; connected: boolean; status: string;
};

export type Statement = {
  step: number; agent: string; decision: string; rationale: string;
  data?: Record<string, unknown>; station?: string;
};

export type Prices = Record<string, { price: number; change_pct: number; volume: number }>;

export type AppState = {
  mode: string;
  emergency_stop: boolean;
  status: Record<string, unknown>;
  limits: Record<string, string | boolean>;
  stations: Station[];
  market: { prices: Prices; updated_at: number | null; stale: boolean };
  balance: { available_usdc: number | null; source: string; updated_at: number | null };
  risk_profile?: Record<string, unknown>;
  safety?: { emergency_stop: { active: boolean; reason: string; since: string }; unresolved_orders: string[] };
  seq: number;
};

export type WsEvent = {
  seq: number; kind: string; ts: number; id?: string; payload: Record<string, any>;
};

export type ScannerToken = {
  name: string; address: string; network: string; mc_or_fdv: number | null;
  uncertain: boolean; category: string; liquidity_usd: number | null;
  volume_24h: number | null; risk: string; veto: boolean; flags: string[];
  sellable: boolean | null; enriched: boolean;
};

export type Readiness = {
  verdict: string; passed: number; total: number; live_autonomous_enabled: boolean;
  mode: string; emergency_stop: boolean; failed: string[]; note: string; connector_note?: string;
  criteria: { number: number; key: string; title: string; passed: boolean; evidence: string[] }[];
};

export type LiveOverview = {
  mode: string; is_live: boolean; real_balance_usdc: number | null; balance_source: string;
  allocated_capital_usdc: string; realised_pnl_usdc: string; daily_pnl_usdc: string;
  unrealised_pnl_usdc: string | null; total_pnl_usdc: string | null; trading_fees_usdc: string;
  open_positions: { product_id: string; base_size: string; cost_usdc: string; partial?: boolean;
    unrealised_pnl_usdc: string | null }[];
  order_history: { client_order_id: string; side?: string; product_id?: string;
    outcome?: { state?: string; side?: string } }[];
  note: string;
};
