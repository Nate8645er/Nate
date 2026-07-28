#!/usr/bin/env python3
"""Let'sDrink 2-in-1: Wasser und Futter. Studio-Look, drei Fassungen."""
import os
from build_b import build, hero, OUT

VARIANTS = [
    dict(name="ad-C1-wasser-futter.png", accent="teal", seed=71,
         size=(1080, 1350), hero_w=0.34, hero_h=0.38, hero_y=0.135,
         head_size=0.066, kicker="LET'SDRINK  ·  2 IN 1",
         head=["Wasser und Futter.", "Eine Flasche."],
         sub=["Der Napf nimmt beides: Wasser aus der Flasche oder eine",
              "Portion Trockenfutter für die Pause unterwegs."],
         chips=["Wasser", "Futter", "550 ml"],
         footer="Gratisversand  ·  14 Tage Rückgabe"),

    dict(name="ad-C2-pause.png", accent="pine", seed=82,
         size=(1080, 1350), hero_w=0.35, hero_h=0.39, hero_y=0.130,
         head_size=0.070, kicker="FÜR DIE PAUSE UNTERWEGS",
         head=["Trinken und", "fressen."],
         sub=["Auf der Wanderung, im Auto, am Bahnhof. Ein Napf,",
              "der immer dabei ist, und eine Hand genügt."],
         chips=["Einhandbedienung", "Wasser und Futter"],
         footer="Versand aus der Schweiz"),

    dict(name="ad-C3-zwei-aufgaben.png", accent="deep", seed=93,
         size=(1080, 1350), hero_w=0.33, hero_h=0.37, hero_y=0.140,
         head_size=0.072, kicker="ZWEI AUFGABEN, EIN GERÄT",
         head=["Napf für Wasser.", "Napf für Futter."],
         sub=["Kein zweites Schüsselchen im Rucksack, kein nasser Boden.",
              "Was du nicht brauchst, läuft zurück in die Flasche."],
         chips=["550 ml", "Auslaufsicher", "6 Farben"],
         footer="Gratisversand  ·  14 Tage Rückgabe"),
]

for v in VARIANTS:
    build(v, hero).save(os.path.join(OUT, v["name"]), "PNG", optimize=True)
print("fertig")
