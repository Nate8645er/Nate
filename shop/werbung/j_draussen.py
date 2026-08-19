# -*- coding: utf-8 -*-
"""Entwurf J und K - die beiden Motive, auf denen getrunken wird.

WARUM ES DIESE MOTIVE GIBT

Nate am 19.8.2026: "Wrstell neue bilder und mach draus werbe bilder."

Neue Bilder ERZEUGEN geht heute nicht, und zwar aus zwei Gruenden:

  1. Die Flasche selbst darf nicht erzeugt sein. Wer bestellt, muss
     bekommen, was er gesehen hat. Erzeugte Umgebung mit echter Flasche
     waere erlaubt gewesen - siehe Punkt 2.
  2. Das Guthaben reicht nicht. Nachgesehen: 1.29 Credits vorhanden,
     eine Aufnahme in marketing_studio_image kostet 2. Also nicht
     einmal ein einziges Bild.

Deshalb dieselbe Aufgabe aus vorhandenem Material geloest. Im Ordner
"tiere" lagen vier Fotos aus Nates eigenem Shop, zwei davon waren
bisher unbenutzt. Beide zeigen genau das, was auf den sieben
Studio-Motiven fehlt: ein Tier, das aus dem angebauten Napf trinkt.

  J   tiere/letsdrink-spaziergang.jpg    Vizsla trinkt im Park aus dem
      tuerkisen Napf, die Hand haelt die Flasche waagrecht. Gegen den
      Freisteller geprueft: klarer Koerper, tuerkiser Napf, Pfotenknopf
      und die beiden Schloss-Zeichen - dieselbe Flasche.
  K   tiere/letsdrink-wanderung-hund.jpg Hund und Wanderer vor den
      Berner Alpen. Gleiche Flasche, gleicher Napf.

WARUM K WICHTIGER IST ALS ER AUSSIEHT

Der Laden verkauft in die Schweiz. Auf keinem der bisher neun Motive
war die Schweiz zu sehen. K zeigt einen Bergweg, Enzian und ein
Alpenpanorama - das erkennt ein Schweizer Kaeufer in einer Zehntel-
sekunde, und keine der deutschen Vergleichsanzeigen hat so ein Bild.

WAS NICHT DRAUFSTEHT

Kein Wort ueber Dichtigkeit, Material, Masse, Gewicht oder Spuelmaschine
- dazu liegt nichts Belegtes vor. Nur 550 ml, sechs Farben, Gratis-
versand und die Zeile "Fuer Hund und Katze", damit auch auf den beiden
Hundemotiven steht, dass es fuer beide Tiere ist.
"""
from h_tiere import alle_drei

# --- J: der Alltag - Spaziergang, Hund trinkt aus dem Napf --------------
J_KOPF = ["Trinken,", "ohne Napf", "zu suchen."]
J_SUB = "Für Hund und Katze  ·  550 ml"
J_BILD = "letsdrink-spaziergang.jpg"

# --- K: die Schweiz - Bergweg, dasselbe Geraet weit oben ----------------
K_KOPF = ["Mit auf", "die Wanderung."]
K_SUB = "Für Hund und Katze  ·  Gratisversand in der Schweiz"
K_BILD = "letsdrink-wanderung-hund.jpg"


if __name__ == "__main__":
    alle_drei(bild=J_BILD, anker=0.30, kopf=J_KOPF, unterzeile=J_SUB,
              praefix="J-spaziergang")
    alle_drei(bild=K_BILD, anker=0.35, kopf=K_KOPF, unterzeile=K_SUB,
              praefix="K-berg")
