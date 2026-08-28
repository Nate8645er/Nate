#!/usr/bin/env python3
# Feierabend - einen Betrieb anlegen.
#
# Bewusst ein Kommandozeilenwerkzeug und keine Selbstregistrierung: Die
# ersten Kunden werden von Hand aufgeschaltet, waehrend du mit ihnen
# sprichst. Eine Registrierungsstrecke fuer null Kunden zu bauen ist die
# teuerste Art, beschaeftigt auszusehen.
#
#   python3 einrichten.py "Malerei Huber" Nate Kevin Sandro

import sys

import db


def main(argumente):
    if len(argumente) < 2:
        print("Aufruf: python3 einrichten.py \"<Betrieb>\" "
              "<Mitarbeiter> [<Mitarbeiter> ...]")
        return 1

    db.anlegen()
    name = argumente[0]
    betrieb_id = "".join(c.lower() if c.isalnum() else "-"
                         for c in name).strip("-")[:40]

    if db.betrieb_lesen(betrieb_id):
        print("Betrieb '%s' existiert bereits." % betrieb_id)
    else:
        db.betrieb_anlegen(betrieb_id, name)
        print("Betrieb angelegt: %s (%s)" % (name, betrieb_id))

    print()
    print("Zugangscodes - jedem Mitarbeiter EINEN geben:")
    print("-" * 46)
    for mitarbeiter in argumente[1:]:
        eintrag = db.mitarbeiter_anlegen(betrieb_id, mitarbeiter)
        print("  %-18s %s" % (eintrag["name"], eintrag["code"]))
    print("-" * 46)
    print()
    print("bexio verbinden (einmalig, mit einem der Codes):")
    print("  <URL>/bexio/verbinden?code=<CODE>")
    print()
    print("Ohne bexio: Kunden von Hand anlegen, sonst kann die")
    print("Pseudonymisierung keine Namen erkennen.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
