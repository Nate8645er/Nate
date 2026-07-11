# Unternehmens-Modul in nate-os einbauen (Modul 9)

Wie beim Factory-Addon: Ordner in den bestehenden nate-os-Plugin-Ordner kopieren.

    skills/unternehmen/  -> nate-os/skills/unternehmen/
    commands/firma.md    -> nate-os/commands/firma.md

Dann in der nate-os SKILL.md:
a) Trigger ergaenzen in der description:  , /firma, /org
b) Router-Zeile ergaenzen:
   | Aufgabe beruehrt mehrere Module / Zustaendigkeit unklar | Modul 9 via /firma | Organigramm routet |

Voraussetzung: Factory-Addon (Modul 8) ist bereits installiert — das Organigramm
referenziert die 4 Factory-Agents.

Test: /firma 50 Meta-Ad-Varianten fuer Luna, Quality Bar mit Vertriebler und Skeptiker abstimmen
