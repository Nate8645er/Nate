import type { WsEvent } from "./types";

type Handler = (e: WsEvent) => void;
type StatusHandler = (s: "connecting" | "open" | "closed") => void;

/**
 * WebSocket client with automatic reconnect, heartbeat watchdog, sequence
 * tracking and de-duplication. On reconnect it resumes from the last sequence
 * number so no event is lost and none is applied twice. While disconnected it
 * emits nothing, so the UI never shows invented real-time data.
 */
export class EventStream {
  private socket: WebSocket | null = null;
  private handlers = new Set<Handler>();
  private statusHandlers = new Set<StatusHandler>();
  private lastSeq = 0;
  private seen = new Set<number>();
  private retry = 0;
  private timer: number | null = null;
  private watchdog: number | null = null;
  private closedByUser = false;

  constructor(private token: string) {}

  onEvent(h: Handler) { this.handlers.add(h); return () => this.handlers.delete(h); }
  onStatus(h: StatusHandler) { this.statusHandlers.add(h); return () => this.statusHandlers.delete(h); }
  get sequence() { return this.lastSeq; }

  private setStatus(s: "connecting" | "open" | "closed") {
    this.statusHandlers.forEach((h) => h(s));
  }

  connect() {
    this.closedByUser = false;
    this.setStatus("connecting");
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/ws?token=${encodeURIComponent(this.token)}&since=${this.lastSeq}`;
    const socket = new WebSocket(url);
    this.socket = socket;

    socket.onopen = () => { this.retry = 0; this.setStatus("open"); this.armWatchdog(); };
    socket.onmessage = (msg) => {
      this.armWatchdog();
      let event: WsEvent;
      try { event = JSON.parse(msg.data as string); } catch { return; }
      if (typeof event.seq !== "number") return;
      if (this.seen.has(event.seq)) return;      // duplicate -> drop
      this.seen.add(event.seq);
      if (this.seen.size > 2000) this.seen = new Set([...this.seen].slice(-1000));
      if (event.seq > this.lastSeq) this.lastSeq = event.seq;
      if (event.kind === "heartbeat" || event.kind === "sync") return;
      this.handlers.forEach((h) => h(event));
    };
    socket.onclose = () => { this.setStatus("closed"); this.scheduleReconnect(); };
    socket.onerror = () => { try { socket.close(); } catch { /* ignore */ } };
  }

  /** The server sends a heartbeat every 15s; if 40s pass, force a reconnect. */
  private armWatchdog() {
    if (this.watchdog) window.clearTimeout(this.watchdog);
    this.watchdog = window.setTimeout(() => {
      try { this.socket?.close(); } catch { /* ignore */ }
    }, 40000);
  }

  private scheduleReconnect() {
    if (this.closedByUser || this.timer) return;
    const delay = Math.min(1000 * 2 ** this.retry++, 15000);
    this.timer = window.setTimeout(() => { this.timer = null; this.connect(); }, delay);
  }

  close() {
    this.closedByUser = true;
    if (this.timer) window.clearTimeout(this.timer);
    if (this.watchdog) window.clearTimeout(this.watchdog);
    try { this.socket?.close(); } catch { /* ignore */ }
  }
}
