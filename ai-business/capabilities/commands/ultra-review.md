---
description: Fuehrt die ULTRA-Qualitaets-Gates (QA + Security + Architektur) auf den aktuellen Aenderungen aus
argument-hint: "[optional: Pfad oder Fokus]"
---

Fuehre die drei Qualitaets-Gates des ULTRA AI ENTERPRISE OS auf den
aktuellen Aenderungen aus (uncommitted Diff; falls leer, letzter Commit).
Fokus/Einschraenkung, falls angegeben: $ARGUMENTS

Gate 1 — QA: Funktioniert es? Tests vorhanden und gruen (real ausfuehren)?
Edge Cases abgedeckt (leer, null, riesig, Unicode, Fehlerpfade)?

Gate 2 — Security (defensiv): Injection, Auth/Berechtigungen, Secrets im
Code, Datenexposition, unsichere Abhaengigkeiten, permissive Konfiguration.
Jeden Befund mit Datei:Zeile und konkretem Szenario belegen.

Gate 3 — Architektur: Einfachste passende Loesung? Duplikation? Skaliert
und erweiterbar? Passt zu den Konventionen des Projekts?

Regeln:
- Nur verifizierte Befunde, ehrlich nach Schweregrad sortiert.
- Bei Befunden: Fix vorschlagen; nur nach Zustimmung anwenden, ausser
  der Nutzer hat den Fix bereits beauftragt.
- Ergebnis: Befundliste ODER explizit "alle drei Gates bestanden".
