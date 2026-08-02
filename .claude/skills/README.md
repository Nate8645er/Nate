# Projekt-Skills

Ordner hier sind entweder eigenstaendige Skills oder **Symlinks** in die
Plugin-Verzeichnisse im Wurzelverzeichnis:

- `design-skillstack/skills/*` (22 Skills)
- `threejs-skills/skills/*` (10 Skills)

Grund fuer die Symlinks: Plugins aus `.claude/settings.json` werden erst beim
Start einer Sitzung geladen. Skills unter `.claude/skills/` werden dagegen
sofort erkannt. Die Verlinkung macht die Plugin-Skills damit auch in einer
bereits laufenden Sitzung nutzbar — ohne den Inhalt zu duplizieren.

Es gibt weiterhin genau eine Quelle pro Skill. Wird ein Skill im Plugin
geaendert, gilt die Aenderung ueber den Symlink automatisch mit.
