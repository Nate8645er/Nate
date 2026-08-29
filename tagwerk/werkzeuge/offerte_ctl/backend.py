# offerte_ctl - Backend: LibreOffice headless.
#
# Nach der cli-anything-Methodik, Phase 3: ein Modul, das die echte
# Anwendung kapselt. Der Rest des Werkzeugs weiss nichts von LibreOffice.
#
# LibreOffice headless hat drei Eigenheiten, die jeden ueberraschen, der
# es zum ersten Mal skriptet - alle drei sind hier abgefangen:
#
#   1. Es meldet "failed to launch javaldx" und funktioniert trotzdem.
#      Diese Warnung ist kein Fehler und wird ignoriert.
#   2. Es gibt bei Fehlern haeufig Rueckgabewert 0 zurueck. Verlassen kann
#      man sich nur darauf, ob die Zieldatei danach existiert.
#   3. Zwei gleichzeitige Aufrufe stolpern ueber dasselbe Benutzerprofil.
#      Deshalb bekommt jeder Aufruf ein eigenes, wegwerfbares Profil.

import os
import shutil
import subprocess
import tempfile

ZEITLIMIT = 180


class BackendFehler(Exception):
    """LibreOffice nicht verfuegbar oder Umwandlung fehlgeschlagen."""


def soffice_pfad():
    for name in ("soffice", "libreoffice"):
        pfad = shutil.which(name)
        if pfad:
            return pfad
    return None


def verfuegbar():
    return soffice_pfad() is not None


def version():
    pfad = soffice_pfad()
    if not pfad:
        return None
    try:
        r = subprocess.run([pfad, "--headless", "--version"],
                           capture_output=True, text=True, timeout=60)
    except (subprocess.SubprocessError, OSError):
        return None
    for zeile in (r.stdout or "").splitlines():
        if zeile.strip().startswith("LibreOffice"):
            return zeile.strip()
    return None


def nach_pdf(quelle, ausgabe_ordner):
    """ODT nach PDF wandeln. Gibt den Pfad der PDF zurueck.

    Prueft das Ergebnis an der Datei, nicht am Rueckgabewert - siehe
    Eigenheit 2 oben.
    """
    pfad = soffice_pfad()
    if not pfad:
        raise BackendFehler(
            "LibreOffice ist nicht installiert. Ohne es kann keine PDF "
            "erzeugt werden - die ODT-Datei entsteht trotzdem.")
    if not os.path.exists(quelle):
        raise BackendFehler("Quelldatei fehlt: %s" % quelle)

    os.makedirs(ausgabe_ordner, exist_ok=True)
    erwartet = os.path.join(
        ausgabe_ordner,
        os.path.splitext(os.path.basename(quelle))[0] + ".pdf")
    if os.path.exists(erwartet):
        os.remove(erwartet)

    # Eigenes Profil je Aufruf, siehe Eigenheit 3.
    profil = tempfile.mkdtemp(prefix="offerte_lo_")
    try:
        r = subprocess.run(
            [pfad, "--headless", "--norestore",
             "-env:UserInstallation=file://%s" % profil,
             "--convert-to", "pdf", "--outdir", ausgabe_ordner, quelle],
            capture_output=True, text=True, timeout=ZEITLIMIT)
    except subprocess.TimeoutExpired:
        raise BackendFehler(
            "LibreOffice hat nach %d Sekunden nicht geantwortet." % ZEITLIMIT)
    except OSError as e:
        raise BackendFehler("LibreOffice liess sich nicht starten: %s" % e)
    finally:
        shutil.rmtree(profil, ignore_errors=True)

    if not os.path.exists(erwartet):
        meldung = (r.stderr or r.stdout or "").strip()
        # Die javaldx-Warnung ist Rauschen und wuerde nur verwirren.
        meldung = "\n".join(z for z in meldung.splitlines()
                            if "javaldx" not in z)
        raise BackendFehler(
            "PDF wurde nicht erzeugt.%s"
            % (" LibreOffice meldet: " + meldung if meldung else ""))
    return erwartet
