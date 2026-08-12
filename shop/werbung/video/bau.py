#!/usr/bin/env python3
"""
Setzt die Marke auf die rohen Higgsfield-Klips.

Aufbau je Werbevideo, immer gleich:
  0.0 s  Klip startet, nackt
  0.4 s  Ecklogo blendet auf und bleibt
  1.2 s  Aussage unten links blendet auf
  4.0 s  Aussage blendet wieder ab, damit sie nicht in den Abspann laeuft
  4.5 s  Ueberblendung in den Abspann, halbe Sekunde
  6.8 s  Ende

Der Ton wird verworfen. Was Kling erzeugt, ist erfundenes Umgebungs-
geraeusch - lieber stumm ausliefern und die Musik bewusst waehlen, als
einen Klang mitschicken, der nie aufgenommen wurde.
"""
import subprocess, sys, pathlib

FF = "/usr/local/lib/python3.11/dist-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
M = pathlib.Path("../marke").resolve()

KLIP_S = 5.0     # Nutzlaenge des Rohklips
AB_S = 2.3       # Standzeit Abspann
UEB = 0.5        # Ueberblendung

# (Rohdatei, Aussagekarte, Ausgabename)
WERBUNG = [
    ("v1.mp4", "satz1.png", "letsdrink-wald-9x16.mp4"),
    ("v2.mp4", "satz2.png", "letsdrink-farben-9x16.mp4"),
    ("v6.mp4", "satz3.png", "letsdrink-unterwegs-9x16.mp4"),
    ("v4.mp4", "satz4.png", "letsdrink-napf-9x16.mp4"),
]


def bau(roh, satz, ziel):
    if not pathlib.Path(roh).exists():
        print("fehlt, uebersprungen: %s" % roh)
        return False

    # Zwei Durchgaenge statt einer Filterkette. Der Grund ist nuechtern:
    # xfade verlangt von beiden Eingaengen eine konstante Bildrate, und
    # eine Standbild-Quelle im selben Filtergraph liefert die nicht
    # zuverlaessig. Zwei fertig kodierte Zwischendateien haben sie immer.
    zw_klip, zw_ab = "_zw_klip.mp4", "_zw_ab.mp4"

    stufe1 = [
        FF, "-v", "error", "-y",
        "-i", roh,
        "-loop", "1", "-framerate", "30", "-t", str(KLIP_S), "-i", str(M / "ecke.png"),
        "-loop", "1", "-framerate", "30", "-t", str(KLIP_S), "-i", str(M / satz),
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,trim=0:%(k)s,setpts=PTS-STARTPTS,fps=30[grund];"
        "[1:v]format=rgba,fade=in:st=0.4:d=0.5:alpha=1[logo];"
        "[2:v]format=rgba,fade=in:st=1.2:d=0.6:alpha=1,"
        "fade=out:st=4.0:d=0.5:alpha=1[satz];"
        "[grund][logo]overlay=0:0[a];"
        "[a][satz]overlay=0:0,format=yuv420p,fps=30[aus]" % {"k": KLIP_S},
        "-map", "[aus]", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "16", "-preset", "medium", zw_klip,
    ]

    stufe2 = [
        FF, "-v", "error", "-y",
        "-loop", "1", "-framerate", "30", "-t", str(AB_S), "-i", str(M / "abspann.png"),
        "-vf", "format=yuv420p,fps=30", "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium", zw_ab,
    ]

    stufe3 = [
        FF, "-v", "error", "-y", "-i", zw_klip, "-i", zw_ab,
        "-filter_complex",
        "[0:v][1:v]xfade=transition=fade:duration=%(u)s:offset=%(o)s,fps=30[aus]"
        % {"u": UEB, "o": KLIP_S - UEB},
        "-map", "[aus]", "-an",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "slow", "-movflags", "+faststart", ziel,
    ]

    for cmd in (stufe1, stufe2, stufe3):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print("FEHLER %s\n%s" % (ziel, r.stderr[-1200:]))
            return False
    print("gebaut: %s" % ziel)
    return True


if __name__ == "__main__":
    ok = [bau(*w) for w in WERBUNG]
    sys.exit(0 if any(ok) else 1)
