/**
 * TypeScript-Client für das platform-backend ("Beides": Node/TS-Seite).
 *
 * Damit die bestehende Next.js-App (TypeScript) das neue Python-Backend in
 * ihrem eigenen Ökosystem ansprechen kann – additiv, ohne bestehende Module
 * zu ändern. Reiner fetch-Client, dependency-frei; honest not-configured, wenn
 * keine baseUrl gesetzt ist.
 */

export interface ComputeDevice {
  id: string;
  vendor: "nvidia" | "amd" | "apple" | "cpu";
  name: string;
  arch: string | null;
  memory_total_mb: number;
  memory_model: "dedicated" | "unified";
  backends: string[];
  capabilities: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
  env: string;
  services: Record<string, boolean>;
}

export interface ComputeResponse {
  gpu_available: boolean;
  device_count: number;
  devices: ComputeDevice[];
}

export class PlatformBackendNichtKonfiguriert extends Error {
  constructor() {
    super("platform-backend: nicht-konfiguriert (baseUrl fehlt)");
    this.name = "PlatformBackendNichtKonfiguriert";
  }
}

export interface ClientOptions {
  baseUrl?: string;
  /** Bearer-Token (Keycloak) für geschützte Endpunkte. */
  token?: string;
  fetchImpl?: typeof fetch;
}

export class PlatformBackendClient {
  private readonly baseUrl: string | null;
  private readonly token?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: ClientOptions = {}) {
    const url = (opts.baseUrl ?? "").trim().replace(/\/$/, "");
    this.baseUrl = url || null;
    this.token = opts.token;
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  get configured(): boolean {
    return this.baseUrl !== null;
  }

  /** Baut eine absolute URL für einen Pfad (exportiert für Tests). */
  buildUrl(path: string): string {
    if (!this.baseUrl) throw new PlatformBackendNichtKonfiguriert();
    return this.baseUrl + (path.startsWith("/") ? path : "/" + path);
  }

  private async get<T>(path: string): Promise<T> {
    const headers: Record<string, string> = { accept: "application/json" };
    if (this.token) headers.authorization = `Bearer ${this.token}`;
    const res = await this.fetchImpl(this.buildUrl(path), { headers });
    if (!res.ok) throw new Error(`platform-backend ${path}: HTTP ${res.status}`);
    return (await res.json()) as T;
  }

  health(): Promise<HealthResponse> {
    return this.get<HealthResponse>("/health");
  }

  compute(): Promise<ComputeResponse> {
    return this.get<ComputeResponse>("/health/compute");
  }
}
