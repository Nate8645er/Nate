#!/usr/bin/env python3
"""Spiegel bauen: Seite holen, alle CSS/JS-Dateien mitziehen, Verweise
lokal umbiegen. Bilder und Fremdquellen werden NICHT geholt - sie
beeinflussen keine Textfarbe. Der Spiegel dient allein der Messung.
"""
import os, re, subprocess, sys, urllib.parse

BASIS = "https://i0m1xi-h5.myshopify.com"
THEME = "197118132601"
ZIEL = os.path.dirname(os.path.abspath(__file__)) + "/spiegel"
JAR = os.path.dirname(os.path.abspath(__file__)) + "/jar.txt"

SEITEN = {
    "start": "/",
    "produkt": "/products/trinkflasche-napf-hund-katze",
}


def hole(url, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run(
        ["curl", "-s", "-L", "-c", JAR, "-b", JAR, url, "-o", out,
         "-w", "%{http_code}"],
        capture_output=True, text=True)
    return r.stdout.strip()


def main():
    os.makedirs(ZIEL + "/a", exist_ok=True)
    gesehen = {}
    for name, pfad in SEITEN.items():
        url = BASIS + pfad + ("?" if "?" not in pfad else "&") + \
            "preview_theme_id=" + THEME
        html_pfad = ZIEL + "/" + name + ".html"
        code = hole(url, html_pfad)
        html = open(html_pfad, encoding="utf-8", errors="replace").read()
        print(name, code, len(html), re.search(r"<title>(.*?)</title>", html,
                                               re.S).group(1)[:60])

        # alle CSS- und JS-Verweise einsammeln
        for m in re.finditer(r'(?:href|src)="([^"]+\.(?:css|js)[^"]*)"', html):
            roh = m.group(1)
            voll = roh
            if voll.startswith("//"):
                voll = "https:" + voll
            elif voll.startswith("/"):
                voll = BASIS + voll
            elif not voll.startswith("http"):
                continue
            if voll in gesehen:
                continue
            datei = urllib.parse.urlparse(voll).path.split("/")[-1]
            lokal = "a/" + str(len(gesehen)) + "_" + datei
            c = hole(voll, ZIEL + "/" + lokal)
            gesehen[voll] = (lokal, c, roh)

        # Verweise umbiegen
        for voll, (lokal, c, roh) in gesehen.items():
            if c == "200":
                html = html.replace('"' + roh + '"', '"' + lokal + '"')
        open(html_pfad, "w", encoding="utf-8").write(html)

    fehl = [(v, c) for v, (l, c, r) in gesehen.items() if c != "200"]
    print("Dateien geholt:", len(gesehen), "| nicht 200:", len(fehl))
    for v, c in fehl:
        print("   ", c, v[:110])


main()
