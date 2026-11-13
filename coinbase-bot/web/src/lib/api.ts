import type { AppState, ScannerToken } from "./types";

const KEY = "hypergrok_token";
export const getToken = () => localStorage.getItem(KEY) ?? "";
export const setToken = (t: string) => localStorage.setItem(KEY, t);
export const clearToken = () => localStorage.removeItem(KEY);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { ...(init?.headers ?? {}), Authorization: `Bearer ${getToken()}` },
  });
  if (res.status === 401) throw new Error("UNAUTHORIZED");
  if (!res.ok) throw new Error(`${res.status}: ${(await res.text()).slice(0, 180)}`);
  return (await res.json()) as T;
}

export const api = {
  state: () => request<AppState>("/api/state"),
  scanner: () => request<{ available: boolean; generated_at?: string; tokens: ScannerToken[]; reason?: string }>("/api/scanner"),
  runMeeting: (symbol: string) => request<any>(`/api/meeting/run?symbol=${encodeURIComponent(symbol)}`, { method: "POST" }),
  setMode: (mode: string) => request<{ mode: string }>(`/api/mode?mode=${encodeURIComponent(mode)}`, { method: "POST" }),
  emergencyStop: (reason: string) => request<any>(`/api/emergency_stop?reason=${encodeURIComponent(reason)}`, { method: "POST" }),
  refreshBalance: (value: number) => request<any>(`/api/balance/refresh?value=${value}`, { method: "POST" }),
};
