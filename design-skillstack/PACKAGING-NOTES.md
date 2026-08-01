# Packaging-Hinweis

Quelle: https://github.com/freshtechbro/claudedesignskills (Apache-2.0)

Das Original-Repository ist ein Marktplatz mit 27 einzelnen Plugins und einer
Pfadtiefe von 11 Ebenen — damit scheitert der Plugin-Upload ("path more than
10 folders deep").

Fuer dieses Paket wurden die 5 offiziellen Bundles zu einem einzigen Plugin
zusammengefuehrt. Geaendert wurde ausschliesslich die Verzeichnisstruktur:

- alle 22 skills/, 27 agents/ und 45 commands/ liegen jetzt flach unter der
  Plugin-Wurzel (max. Tiefe 6 statt 11)
- eine `.claude-plugin/plugin.json` fasst sie zusammen
- Namenskollisionen gab es keine, es wurde nichts umbenannt

Kein SKILL.md, kein Agent, kein Command und kein Skript wurde inhaltlich
veraendert. LICENSE und README des Originals liegen unveraendert bei.
