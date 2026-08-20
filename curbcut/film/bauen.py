#!/usr/bin/env python3
"""
bauen.py - setzt Folien und Stimme zu einem Film zusammen.

WARUM DIE STIMME LOKAL ERZEUGT WIRD

Der erste Versuch lief ueber einen bezahlten Dienst. Nach genau einer
Sprachspur war das Guthaben leer - 1.29 Credits, und der Rest des Videos
haette weitere 0.90 gekostet, die nicht mehr da waren.

Piper laeuft auf diesem Rechner, kostet nichts und spricht Deutsch. Die
Probe war 4.64 Sekunden lang, die bezahlte Fassung desselben Satzes
4.93 - also spricht es wirklich Deutsch und liest nicht deutschen Text
mit englischer Aussprache vor.

Das ist die bessere Loesung, nicht der Notnagel: Ein Erklaervideo, das
man nur einmal bauen kann, weil danach das Guthaben leer ist, kann man
auch nicht verbessern. Dieses hier kann beliebig oft neu gebaut werden.

DIE LAENGE JEDER FOLIE KOMMT AUS DER TONSPUR

Nicht umgekehrt. Wer feste Sekunden setzt, schneidet entweder den Satz
ab oder laesst das Bild stehen, nachdem die Stimme fertig ist. Beides
sieht nach Bastelei aus.
"""

import os
import subprocess
import wave

HIER = os.path.dirname(os.path.abspath(__file__))
STIMME = os.path.join(HIER, "stimme", "de_DE-thorsten-medium.onnx")
BILDER = os.path.join(HIER, "bilder")
TON = os.path.join(HIER, "ton")
ZIEL = os.path.join(HIER, "curbcut-erklaert.mp4")

# Was auf jeder Folie gesagt wird. Nicht dasselbe wie der Folientext -
# die Folie zeigt, die Stimme erklaert. Wer beides gleich macht, laesst
# den Zuschauer mitlesen statt zuhoeren.
TEXTE = {
    "01": "Curbcut. Das dritte Geschäft. Ich zeige dir, was es ist "
          "und wie du es startest.",
    "02": "Seit Juni zweitausendfünfundzwanzig gilt in Europa ein Gesetz. "
          "Webseiten müssen auch für blinde Menschen benutzbar sein. "
          "Wer das nicht macht, zahlt eine Busse.",
    "03": "Bis hunderttausend Euro. Und das ist keine leere Drohung. "
          "Ein Gericht in Frankreich hat gegen Carrefour fünfhundert Euro "
          "pro Tag verhängt, so lange, bis die Seite in Ordnung ist.",
    "04": "Ich habe achtzehn Schweizer Seiten geprüft. Siebzehn davon "
          "hatten Fehler. Bei zwölf war die Seite wirklich nicht bedienbar.",
    "05": "Curbcut ist wie die MFK, aber für Webseiten. Du gibst eine "
          "Adresse ein, es liest die Seite und sagt dir genau, welche "
          "Stellen kaputt sind. Und dann schaut es jeden Tag nach.",
    "06": "Am Markt gibt es nur zwei Sachen. Billige Widgets ab neun "
          "Franken. Die kleben etwas über die Seite, aber wer prüft, "
          "schaut darunter. Und richtige Lösungen ab vierhundert Dollar, "
          "die kein normaler Betrieb bezahlt. Dazwischen ist nichts. "
          "Genau da sitzen wir.",
    "07": "Der Betrieb kostet dich sechs Franken im Monat. Insgesamt, "
          "nicht pro Kunde. Ein Kunde zahlt neunzehn bis "
          "hundertneunundvierzig. Der erste Kunde deckt die laufenden "
          "Kosten fast dreimal.",
    "08": "Und sie kaufen nicht, weil es schön ist. Sie kaufen, weil sie "
          "Angst vor der Busse haben. Das ist der Unterschied zur "
          "Trinkflasche.",
    "09": "So aktivierst du es. Erstens: die Domain kaufen, rund zwölf "
          "Franken im Jahr. Zweitens: ein Paddle-Konto eröffnen, das nimmt "
          "auch Einzelpersonen ohne Firma. Drittens: sag mir Bescheid, "
          "dann schalte ich die Seite online.",
    "10": "Was ich dir nicht versprechen kann, sind Kunden. Der Wächter "
          "läuft ab heute jeden Tag von selbst. Aber ob dich jemand "
          "findet, das weiss vorher niemand.",
}

NACHKLANG = 0.7      # Sekunden Stille am Ende jeder Folie, damit es
                     # nicht gehetzt wirkt und der Zuschauer die Zahl liest


def sprechen(schluessel, text):
    os.makedirs(TON, exist_ok=True)
    ziel = os.path.join(TON, f"{schluessel}.wav")
    subprocess.run(
        ["python3", "-m", "piper", "-m", STIMME, "-f", ziel],
        input=text.encode("utf-8"), check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return ziel


def dauer(pfad):
    with wave.open(pfad) as w:
        return w.getnframes() / w.getframerate()


def bauen():
    stuecke = []
    print("  Stimme erzeugen:")
    for schluessel in sorted(TEXTE):
        bild = os.path.join(BILDER, f"{schluessel}.png")
        if not os.path.exists(bild):
            print(f"    {schluessel}: Bild fehlt, uebersprungen")
            continue
        ton = sprechen(schluessel, TEXTE[schluessel])
        d = dauer(ton) + NACHKLANG
        stuecke.append((bild, ton, d))
        print(f"    {schluessel}  {d:5.2f}s")

    gesamt = sum(d for _, _, d in stuecke)
    print(f"\n  Gesamt: {gesamt:.0f} Sekunden, {len(stuecke)} Folien")

    # Jede Folie einzeln zu einem Stueck, dann aneinanderhaengen.
    # Ein einziger ffmpeg-Aufruf mit filter_complex waere kuerzer, aber
    # wenn er scheitert, weiss man nicht, an welcher Folie.
    teile = []
    for i, (bild, ton, d) in enumerate(stuecke):
        aus = os.path.join(TON, f"teil{i:02d}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", bild, "-i", ton,
            "-filter_complex",
            f"[1:a]apad=pad_dur={NACHKLANG}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-t", f"{d:.3f}", "-shortest", aus,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        teile.append(aus)
        print(f"    Teil {i+1}/{len(stuecke)}")

    liste = os.path.join(TON, "liste.txt")
    with open(liste, "w") as f:
        for t in teile:
            f.write(f"file '{os.path.abspath(t)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", liste,
        "-c", "copy", ZIEL,
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for t in teile:
        os.remove(t)
    return ZIEL, gesamt


if __name__ == "__main__":
    pfad, laenge = bauen()
    groesse = os.path.getsize(pfad) / 1_000_000
    print(f"\n  {pfad}")
    print(f"  {laenge:.0f} Sekunden, {groesse:.1f} MB")
