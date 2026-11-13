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
