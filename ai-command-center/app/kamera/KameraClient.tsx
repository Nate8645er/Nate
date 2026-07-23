"use client";

/**
 * Kamera & Bild – nimmt ein Foto per Gerätekamera auf ODER lädt ein Bild hoch
 * und lässt es von der KI beschreiben/auswerten (POST /api/bild). Funktioniert
 * mit einem bild-fähigen Modell (ANTHROPIC_API_KEY); ohne Key ehrlicher Hinweis.
 *
 * Reine Browser-APIs (getUserMedia, canvas, FileReader) – keine Abhängigkeiten.
 */

import { useCallback, useRef, useState } from "react";

export default function KameraClient() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [kameraAn, setKameraAn] = useState(false);
  const [bild, setBild] = useState<string | null>(null);
  const [frage, setFrage] = useState("");
  const [ergebnis, setErgebnis] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [laeuft, setLaeuft] = useState(false);

  const kameraStarten = useCallback(async () => {
    setFehler(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setKameraAn(true);
    } catch {
      setFehler("Keine Kamera verfügbar oder Zugriff abgelehnt. Sie können stattdessen ein Bild hochladen.");
    }
  }, []);

  const kameraStoppen = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setKameraAn(false);
  }, []);

  const fotoAufnehmen = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    const canvas = document.createElement("canvas");
    canvas.width = v.videoWidth || 1280;
    canvas.height = v.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
    setBild(canvas.toDataURL("image/jpeg", 0.85));
    setErgebnis(null);
    kameraStoppen();
  }, [kameraStoppen]);

  function bildHochladen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setFehler("Bitte ein Bild wählen (JPG, PNG, WEBP).");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setBild(typeof reader.result === "string" ? reader.result : null);
      setErgebnis(null);
      setFehler(null);
    };
    reader.readAsDataURL(file);
  }

  async function analysieren() {
    if (!bild) return;
    setLaeuft(true);
    setFehler(null);
    setErgebnis(null);
    try {
      const res = await fetch("/api/bild", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bild, frage }),
      });
      const data = (await res.json()) as { text?: string; error?: string };
      if (res.ok && data.text) {
        setErgebnis(data.text);
      } else if (res.status === 501) {
        setFehler("Bildanalyse wird aktiv, sobald ein bild-fähiges Modell verbunden ist (ANTHROPIC_API_KEY).");
      } else {
        setFehler("Analyse fehlgeschlagen. Bitte anderes Bild versuchen.");
      }
    } catch {
      setFehler("Netzwerkfehler.");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold tracking-tight">
        Kamera &amp; <span className="acc-grad-text">Bild</span>
      </h1>
      <p className="mt-2 text-sm text-[#6f6557]">
        Foto aufnehmen oder Bild hochladen – die KI beschreibt es und liest sichtbaren Text
        (z. B. Beleg, Notiz, Whiteboard, Produktfoto).
      </p>

      <div className="acc-card mt-6 rounded-2xl p-5">
        <div className="flex flex-wrap gap-3">
          {!kameraAn ? (
            <button type="button" onClick={kameraStarten} className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white hover:brightness-105">
              Kamera starten
            </button>
          ) : (
            <button type="button" onClick={fotoAufnehmen} className="rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white hover:brightness-105">
              Foto aufnehmen
            </button>
          )}
          <label className="cursor-pointer rounded-full border border-[#e0d8c6] bg-white px-5 py-2.5 text-sm font-semibold text-[#1c1917] hover:border-[#ffb066] hover:text-[#c25e0e]">
            Bild hochladen
            <input type="file" accept="image/*" capture="environment" onChange={bildHochladen} className="hidden" />
          </label>
          {kameraAn && (
            <button type="button" onClick={kameraStoppen} className="rounded-full border border-[#e0d8c6] bg-white px-5 py-2.5 text-sm font-semibold text-[#4a4335]">
              Kamera aus
            </button>
          )}
        </div>

        {/* Live-Kamera */}
        <video ref={videoRef} playsInline muted className={`mt-4 w-full rounded-xl border border-[#e8e1d2] ${kameraAn ? "" : "hidden"}`} />

        {/* Aufgenommenes/hochgeladenes Bild */}
        {bild && !kameraAn && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={bild} alt="Aufgenommenes Bild" className="mt-4 w-full rounded-xl border border-[#e8e1d2]" />
        )}

        {fehler && <p className="mt-4 rounded-xl border border-[#f0d9a8] bg-[#fdf8ee] px-4 py-3 text-sm text-[#8a6a2f]">{fehler}</p>}

        {bild && !kameraAn && (
          <div className="mt-4">
            <label className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Frage zum Bild (optional)</label>
            <input
              type="text"
              value={frage}
              onChange={(e) => setFrage(e.target.value)}
              placeholder="z. B. Welcher Betrag steht auf dem Beleg?"
              className="mt-1 w-full rounded-xl border border-[#e0d8c6] bg-white px-4 py-2.5 text-sm"
            />
            <button
              type="button"
              onClick={analysieren}
              disabled={laeuft}
              className="mt-3 rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2.5 text-sm font-bold text-white hover:brightness-105 disabled:opacity-60"
            >
              {laeuft ? "Analysiere …" : "Bild analysieren"}
            </button>
          </div>
        )}

        {ergebnis && (
          <div className="mt-5 rounded-2xl border border-[#bfe6cf] bg-[#f0faf4] p-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-[#177245]">Ergebnis</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-[#1c1917]">{ergebnis}</p>
          </div>
        )}
      </div>
    </div>
  );
}
