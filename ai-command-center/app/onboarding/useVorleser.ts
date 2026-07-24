"use client";

/**
 * Deutsche Sprachführung über die Web-Speech-API des Browsers (SpeechSynthesis).
 *
 * Liest eine Folge von Texten (z. B. Onboarding-Schritte) nacheinander in
 * Deutsch vor und meldet, welcher Eintrag gerade gesprochen wird – so kann die
 * UI den aktiven Schritt hervorheben. Alles läuft lokal im Browser: keine
 * Server, keine Kosten, keine Datenweitergabe.
 *
 * Bewusst defensiv: Fehlt die API (SSR, alte Browser, kein Sprachpaket), meldet
 * `unterstuetzt=false` und alle Aktionen sind wirkungslose No-ops – nie ein
 * Absturz, die Seite funktioniert ohne Stimme normal weiter.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export interface VorleserStatus {
  /** Ob der Browser Sprachausgabe kann UND eine Stimme bereitsteht. */
  unterstuetzt: boolean;
  /** Wird gerade vorgelesen? */
  spricht: boolean;
  /** Index des aktuell gesprochenen Eintrags (oder null, wenn still). */
  aktiverIndex: number | null;
  /**
   * Liest die Texte nacheinander vor. Optionale `intro` wird ohne
   * Schritt-Hervorhebung vorangestellt (z. B. Begrüssung + Tarif-Inhalt),
   * danach werden die Schritte mit Hervorhebung gesprochen.
   */
  vorlesen: (texte: string[], opts?: { intro?: string }) => void;
  /** Liest genau einen Text (mit Index für die Hervorhebung). */
  einzeln: (text: string, index: number) => void;
  /** Bricht die Ausgabe sofort ab. */
  stopp: () => void;
}

/** Beste passende deutsche Stimme wählen (bevorzugt de-DE, sonst irgendeine de-*). */
function deutscheStimme(
  stimmen: SpeechSynthesisVoice[],
): SpeechSynthesisVoice | undefined {
  return (
    stimmen.find((s) => s.lang === "de-DE") ??
    stimmen.find((s) => s.lang?.toLowerCase().startsWith("de"))
  );
}

export function useVorleser(): VorleserStatus {
  const [unterstuetzt, setUnterstuetzt] = useState(false);
  const [spricht, setSpricht] = useState(false);
  const [aktiverIndex, setAktiverIndex] = useState<number | null>(null);
  const stimmeRef = useRef<SpeechSynthesisVoice | undefined>(undefined);
  // Merkt sich den laufenden Auftrag, damit ein Abbruch die Kette stoppt.
  const laufRef = useRef(0);

  // Verfügbarkeit + Stimmen ermitteln (Stimmen laden teils asynchron nach).
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const synth = window.speechSynthesis;

    const stimmenLaden = () => {
      const gefunden = deutscheStimme(synth.getVoices());
      stimmeRef.current = gefunden;
      setUnterstuetzt(!!gefunden);
    };

    stimmenLaden();
    synth.addEventListener("voiceschanged", stimmenLaden);
    return () => {
      synth.removeEventListener("voiceschanged", stimmenLaden);
      synth.cancel();
    };
  }, []);

  const stopp = useCallback(() => {
    laufRef.current += 1; // laufende Kette entwerten
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpricht(false);
    setAktiverIndex(null);
  }, []);

  const aeussern = useCallback((text: string): SpeechSynthesisUtterance => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "de-DE";
    if (stimmeRef.current) u.voice = stimmeRef.current;
    u.rate = 1; // natürliche Vorlesegeschwindigkeit
    u.pitch = 1;
    return u;
  }, []);

  const vorlesen = useCallback(
    (texte: string[], opts?: { intro?: string }) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      const synth = window.speechSynthesis;
      synth.cancel();
      const lauf = ++laufRef.current;
      setSpricht(true);

      const sprich = (i: number) => {
        // Auftrag veraltet (Stopp oder neuer Start) → abbrechen.
        if (lauf !== laufRef.current) return;
        if (i >= texte.length) {
          setSpricht(false);
          setAktiverIndex(null);
          return;
        }
        setAktiverIndex(i);
        const u = aeussern(texte[i]);
        u.onend = () => sprich(i + 1);
        u.onerror = () => sprich(i + 1); // nicht hängenbleiben
        synth.speak(u);
      };

      // Optionale Einleitung zuerst, ohne einen Schritt hervorzuheben.
      if (opts?.intro) {
        setAktiverIndex(null);
        const ein = aeussern(opts.intro);
        ein.onend = () => sprich(0);
        ein.onerror = () => sprich(0);
        synth.speak(ein);
      } else {
        sprich(0);
      }
    },
    [aeussern],
  );

  const einzeln = useCallback(
    (text: string, index: number) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      const synth = window.speechSynthesis;
      synth.cancel();
      const lauf = ++laufRef.current;
      setSpricht(true);
      setAktiverIndex(index);
      const u = aeussern(text);
      const fertig = () => {
        if (lauf !== laufRef.current) return;
        setSpricht(false);
        setAktiverIndex(null);
      };
      u.onend = fertig;
      u.onerror = fertig;
      synth.speak(u);
    },
    [aeussern],
  );

  return { unterstuetzt, spricht, aktiverIndex, vorlesen, einzeln, stopp };
}
