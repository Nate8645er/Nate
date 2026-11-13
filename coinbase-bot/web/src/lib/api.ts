import type { AppState, ScannerToken } from "./types";

const TOKEN_KEY = "hypergrok_session";
const CSRF_KEY = "hypergrok_csrf";
const ROLE_KEY = "hypergrok_role";

export const getToken = () => localStorage.getItem(TOKEN_KEY) ?? "";
export const getCsrf = () => localStorage.getItem(CSRF_KEY) ?? "";
export const getRole = () => localStorage.getItem(ROLE_KEY) ?? "";
export function storeSession(token: string, csrf: string, role: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(CSRF_KEY, csrf);
  localStorage.setItem(ROLE_KEY, role);
}
export function clearSession() {
  [TOKEN_KEY, CSRF_KEY, ROLE_KEY].forEach((k) => localStorage.removeItem(k));
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const method = init?.method ?? "GET";
  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string> | undefined),
    Authorization: `Bearer ${getToken()}`,
  };
  // CSRF: state-changing calls must echo the session token from a header.
  if (method !== "GET") headers["X-CSRF-Token"] = getCsrf();
  const res = await fetch(path, { ...init, headers });
  if (res.status === 401) { clearSession(); throw new Error("UNAUTHORIZED"); }
  if (res.status === 403) throw new Error("FORBIDDEN");
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 180)}`);
  return (await res.json()) as T;
}

export type WhaleIntel = {
  mint: string; supply: number | null; recent_tx_count: number | null;
  window_hours: number | null; tx_per_hour: number | null; activity: string;
  top_holder_pct: string; concentration: string; notes: string[];
};
export type SocialIntel = {
  trending: { name: string; symbol: string; rank: number | null; score: number | null }[];
  source: string; available: boolean; sentiment_score: string; notes: string[];
};

export const api = {
  login: async (username: string, password: string) => {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error("Anmeldung fehlgeschlagen");
    return (await res.json()) as { token: string; csrf: string; role: string; username: string };
  },
  logout: () => request<{ ok: boolean }>("/api/logout", { method: "POST" }),
  state: () => request<AppState>("/api/state"),
  scanner: () => request<{ available: boolean; generated_at?: string; tokens: ScannerToken[]; reason?: string }>("/api/scanner"),
  runMeeting: (symbol: string) => request<any>(`/api/meeting/run?symbol=${encodeURIComponent(symbol)}`, { method: "POST" }),
  setMode: (mode: string) => request<{ mode: string }>(`/api/mode?mode=${encodeURIComponent(mode)}`, { method: "POST" }),
  emergencyStop: (reason: string) => request<any>(`/api/emergency_stop?reason=${encodeURIComponent(reason)}`, { method: "POST" }),
  refreshBalance: (value: number) => request<any>(`/api/balance/refresh?value=${value}`, { method: "POST" }),
  whale: (mint: string) => request<WhaleIntel>(`/api/intel/whale?mint=${encodeURIComponent(mint)}`),
  smartMoney: (mint: string) => request<Record<string, unknown>>(`/api/intel/smart_money?mint=${encodeURIComponent(mint)}`),
  social: () => request<SocialIntel>("/api/intel/social"),
};
