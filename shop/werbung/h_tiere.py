# -*- coding: utf-8 -*-
"""Entwurf H und I - die Motive, auf denen ein Tier zu sehen ist.

WARUM ES DIESE MOTIVE GIBT

Nate am 19.8.2026: "Man soll sehen das es fuer Hund und Katze ist."
Er hat recht. Auf den sieben Studio-Motiven steht nur die Flasche.
Wer sie nicht kennt, sieht eine Trinkflasche und denkt an sich selbst,
nicht an sein Tier. Die Zeile "Fuer Hund und Katze" steht auf allen
sieben - aber lesen ist nicht sehen.

WELCHES BILDMATERIAL - UND WARUM NICHT DAS ANDERE

Geprueft wurde die Flasche auf jedem Bild gegen den echten Freisteller:

  BENUTZT     tiere/letsdrink-hero-banner.jpg   Hund und Katze, sechs
              Flaschen. Klarer Koerper, tuerkiser Napf, Pfotenknopf -
              stimmt mit dem Produkt ueberein.
  BENUTZT     tiere/letsdrink-reisen-katze.jpg  Katze trinkt aus dem
              Napf. Bei 100 Prozent nachgesehen: gleiche Flasche.

  NICHT       shop/werbung/video/letsdrink-film-30s-9x16.mp4
              Der Film zeigt eine Flasche mit CREMEFARBENEM Koerper und
              eingepraegter Pfote. Nates sechs Flaschen haben alle einen
              klaren, durchsichtigen Koerper ohne Pfote. Ein anderes
              Modell. Wer das anklickt und Nates Flasche bekommt,
              schreibt eine Rueckgabe statt einer Empfehlung. Dazu
              nennt sein Abspann katzenufos.com.

ZWEITE FASSUNG - WARUM DER ERSTE AUFBAU WEG IST

Erste Fassung: Foto oben in einem Rechteck, Text unten auf Weiss.
Nate dazu: "Neue werbe bilder dise sehen zu amateur aus." Er hatte
recht, und der Vergleich im eigenen Ordner beweist es - neben A-hand
und B-farben sahen diese Motive wie eine Vorlage aus. Die Naht
zwischen Foto und Textkasten, das tote weisse Feld rechts neben der
Ueberschrift, zwei Haelften ohne gemeinsamen Grund.

Der Aufbau steckt jetzt in lib_foto.py: Foto randlos ueber die ganze
Flaeche, Text darauf, Verlauf dazwischen - und die Deckkraft des
Verlaufs wird gemessen statt geraten. Die Aufloesungsrechnung, die
frueher hier stand, ist damit hinfaellig: die Bilder werden ohnehin
vergroessert, und ein randloses Foto vertraegt das besser als ein
Streifen, in dem jede Kante zu sehen ist.
"""
from lib_foto import alle_drei, alle_drei_hell

# --- H: Hund UND Katze in einem Bild -----------------------------------
H_KOPF = ["Für Hund", "und Katze."]
H_SUB = "550 ml  ·  Sechs Farben"
H_BILD = "letsdrink-hero-banner.jpg"

# --- I: die Katze allein, weil sie die Ueberraschung ist ----------------
I_KOPF = ["Auch für", "die Katze."]
I_SUB = "Ein Napf, der schon dran ist."
I_BILD = "letsdrink-reisen-katze.jpg"


if __name__ == "__main__":
    # H laeuft hell: das Bild ist ein Produktfoto auf hellem Karton, kein
    # Stimmungsbild. Ein dunkler Verlauf laege genau auf den sechs
    # Flaschen - siehe lib_foto.hoch_hell.
    alle_drei_hell(bild=H_BILD, anker=0.30, kopf=H_KOPF, unterzeile=H_SUB,
                   praefix="H-tiere")
    alle_drei(bild=I_BILD, anker=0.30, kopf=I_KOPF, unterzeile=I_SUB,
              praefix="I-katze")
