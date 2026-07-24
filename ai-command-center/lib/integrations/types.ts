/**
 * Integrations-Schicht: optionale, extern gehostete Module, die das bestehende
 * KI-System erweitern (Multi-Agent-Engines, Workflows, lokale Modelle, RAG,
 * Vektor-Speicher, Sprache …). Die App bleibt schlank: jede Integration wird
 * über Umgebungsvariablen aktiviert und per URL angebunden – ohne aktive
 * Konfiguration meldet sie ehrlich „nicht verbunden".
 *
 * WICHTIG: Diese Datei beschreibt nur Metadaten + Anbindung. Die schweren
 * Dienste (Python/Docker/Binaries) hostet der Kunde selbst; Setup siehe
 * INTEGRATIONEN.md. Nichts hier lädt oder startet fremde Software automatisch.
 */

import type { PlanId } from "../agents/types";

/** Fachliche Kategorie der Integration. */
export type IntegrationKind =
  | "multi-agent"
  | "workflow"
  | "local-llm"
  | "computer-use"
  | "browser"
  | "rag"
  | "vector"
  | "voice"
  | "token-opt"
  | "automation" // Steuerung echter Geräte/Abläufe (z. B. Home Assistant, Node-RED)
  | "search" // eigene Suchmaschine als Quelle für den KI-Browser
  | "stt" // Sprache-zu-Text (Transkription)
  | "storage" // Objektspeicher für Dateien/Artefakte
  | "extract"; // Textextraktion aus vielen Dateiformaten

/** Wie die Integration betrieben wird. */
export type Laufzeit =
  | "service" // eigenständiger Dienst (Docker/HTTP-API)
  | "binary" // natives Binary mit HTTP-Schnittstelle (z. B. Ollama)
  | "python" // Python-Dienst
  | "desktop" // Desktop-App (nur lokal, mit GUI/Audio)
  | "lib" // Bibliothek/Build-Zeit-Modul
  | "builtin"; // bereits im System vorhanden

export interface Integration {
  /** Stabile Kennung (kebab). */
  id: string;
  name: string;
  /** Quell-Repository (Open Source). */
  repo: string;
  kind: IntegrationKind;
  /** Kurzer Nutzen auf Deutsch. */
  zweck: string;
  laufzeit: Laufzeit;
  /** Muss der Kunde den Dienst selbst hosten? */
  selbstGehostet: boolean;
  /**
   * Umgebungsvariablen, die zum Aktivieren nötig sind (z. B. Basis-URL).
   * Leer bei `immerAktiv` (builtin/lib brauchen keine externe Anbindung).
   */
  envKeys: string[];
  /** Env-Variable mit der Basis-URL für den Health-Check (optional). */
  healthUrlEnv?: string;
  /** Pfad, der für den Health-Check an die Basis-URL gehängt wird. */
  healthPfad?: string;
  /** Ab dieser Abo-Stufe verfügbar. */
  abStufe: PlanId;
  /** true = ohne externe Konfiguration nutzbar (bereits integriert). */
  immerAktiv?: boolean;
  /** Ehrlicher Hinweis auf Grenzen (z. B. „braucht Audio-Hardware"). */
  hinweis?: string;
}

/** Verbindungs-/Health-Status einer Integration. */
export type IntegrationStatus =
  | "aktiv" // konfiguriert und erreichbar
  | "konfiguriert" // konfiguriert, Health nicht geprüft/erreichbar
  | "bereit" // immerAktiv (kein Setup nötig)
  | "nicht-konfiguriert"; // ENV fehlt
