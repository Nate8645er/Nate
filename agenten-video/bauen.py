#!/usr/bin/env python3
"""
bauen.py - Folien + deutsche Stimme zu einem Film.

Dieselbe Machart wie das Curbcut-Video: Stimme lokal mit Piper (kostet
nichts), Folienlaenge kommt aus der Tonspur, nicht aus fester Sekundenzahl.
Das Stimmmodell liegt beim Curbcut-Film und wird von dort mitbenutzt.
"""

import os
import subprocess
import wave

HIER = os.path.dirname(os.path.abspath(__file__))
STIMME = os.path.join(HIER, "..", "curbcut", "film", "stimme",
                      "de_DE-thorsten-medium.onnx")
BILDER = os.path.join(HIER, "bilder")
TON = os.path.join(HIER, "ton")
ZIEL = os.path.join(HIER, "deine-helfer.mp4")
NACHKLANG = 0.7

TEXTE = {
    "01": "Du hast jetzt ein Team von Helfern. Ich zeige dir kurz, was "
          "sie sind und wie du sie einsetzt.",
    "02": "Ein Agent ist einfach ein Helfer mit einem Beruf. Der eine "
          "kann SEO, der andere schreibt Texte, der dritte beantwortet "
          "Kundenfragen. Du sagst nur, was du brauchst.",
    "03": "Ich habe siebzehn Helfer fuer deinen Shop aktiviert. Weitere "
          "vierundsiebzig liegen im Katalog, falls du sie je brauchst. "
          "Kein Schluessel, kein Passwort noetig.",
    "04": "Dein SEO-Team sorgt dafuer, dass dich Google findet. Der "
          "Keyword-Helfer findet die richtigen Suchwoerter, der "
          "Text-Helfer schreibt die Seite dazu, der Meta-Helfer macht "
          "den Titel im Suchergebnis.",
    "05": "Dein Verkaufs-Team macht aus Besuchern Kunden. Der Sales-Helfer "
          "schreibt Nachfass-Mails, der Support-Helfer beantwortet Fragen, "
          "der Inhalt-Helfer plant, was du wann posten koenntest.",
    "06": "Dein Denk-Team hilft dir beim Entscheiden. Der Startup-Helfer "
          "rechnet Markt und Preise durch, der Analyse-Helfer macht aus "
          "Zahlen eine klare Aussage, der Recherche-Helfer prueft die "
          "Konkurrenz.",
    "07": "So benutzt du sie: Du tippst einfach, was du willst. Zum "
          "Beispiel: Nutz den SEO-Keyword-Helfer und finde die besten "
          "Suchbegriffe fuer die Trinkflasche. Mehr musst du nicht wissen.",
    "08": "Und jetzt ehrlich: Ein Helfer schreibt, aber verkaufen tut er "
          "nicht von selbst. Die Helfer machen die Arbeit schneller. Der "
          "Umsatz haengt zuerst daran, dass die Werbung die richtigen "
          "Leute holt.",
    "09": "Darum das Wichtigste zuerst: erst der Pixel, dann die Helfer. "
          "Sobald die Werbung meldet, wer kauft, machen dich die SEO- und "
          "Text-Helfer richtig gross. Vorher arbeiten sie ins Leere.",
}


def sprechen(k, text):
    os.makedirs(TON, exist_ok=True)
    ziel = os.path.join(TON, f"{k}.wav")
    subprocess.run(["python3", "-m", "piper", "-m", STIMME, "-f", ziel],
                   input=text.encode("utf-8"), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ziel


def dauer(p):
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def bauen():
    stuecke = []
    print("  Stimme:")
    for k in sorted(TEXTE):
        bild = os.path.join(BILDER, f"{k}.png")
        if not os.path.exists(bild):
            continue
        ton = sprechen(k, TEXTE[k])
        d = dauer(ton) + NACHKLANG
        stuecke.append((bild, ton, d))
        print(f"    {k}  {d:5.2f}s")
    gesamt = sum(d for _, _, d in stuecke)
    print(f"  Gesamt: {gesamt:.0f}s\n  Schneide:")
    teile = []
    for i, (bild, ton, d) in enumerate(stuecke):
        aus = os.path.join(TON, f"t{i:02d}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", bild, "-i", ton,
            "-filter_complex", f"[1:a]apad=pad_dur={NACHKLANG}[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset",
            "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-t", f"{d:.3f}", "-shortest", aus,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        teile.append(aus)
        print(f"    {i+1}/{len(stuecke)}")
    liste = os.path.join(TON, "liste.txt")
    with open(liste, "w") as fh:
        for t in teile:
            fh.write(f"file '{os.path.abspath(t)}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                    liste, "-c", "copy", ZIEL], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for t in teile:
        os.remove(t)
    return ZIEL, gesamt


if __name__ == "__main__":
    p, laenge = bauen()
    print(f"\n  {p}\n  {laenge:.0f}s, {os.path.getsize(p)/1_000_000:.1f} MB")
