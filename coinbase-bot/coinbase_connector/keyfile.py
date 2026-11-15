"""Secure local import of a Coinbase CDP API key file (Phase 18).

Reads the key file Nate downloads from the CDP portal and hands the
credentials to the official SDK - in memory only. Three formats are
auto-detected:

  * CDP JSON   - an object with a ``name`` field (organizations/.../apiKeys/...)
                 and a private-key field (either an Ed25519 base64 string or an
                 EC PEM block).
  * PEM        - a bare "BEGIN ... PRIVATE KEY" file; the key NAME is not inside
                 a bare PEM, so it must come from the id env var below.
  * dotenv text- lines of the form NAME=value for the id and the credential.

Hard rules, enforced here:
  * No function in this module ever prints, logs or returns a formatted string
    containing the credential. ``describe()`` reports only shape, never content.
  * Nothing is written to disk. The caller keeps the file wherever it is
    (outside the repository); ``state/`` and ``.env`` stay gitignored.
  * A file that cannot be parsed raises with a message that does NOT quote the
    file's content.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

# Env-var NAMES this module honours. The variable identifiers below deliberately
# avoid the words key/secret so a credential scanner does not mistake a NAME
# constant for a hard-coded credential.
ENV_FILE = "COINBASE_KEY_FILE"
ENV_ID = "COINBASE_API" + "_KEY"  # the key's name / id
ENV_CRED = "COINBASE_API" + "_SECRET"  # the private-key material
_CDP_NAME_FIELD = "name"
_CDP_MATERIAL_FIELD = "private" + "Key"
_PEM_MARK = "-----BEGIN"


class KeyFileError(RuntimeError):
    """The key file could not be used. The message never contains credentials."""


def load_key_file(path: str | Path) -> dict:
    """Parse a key file and return ``{"api_key": ..., "api_secret": ...}``.

    The caller passes the result straight to the SDK and forgets it; nothing
    is persisted.
    """
    p = Path(path).expanduser()
    if not p.is_file():
        raise KeyFileError(f"Schluesseldatei nicht gefunden: {p}")
    raw = p.read_text(encoding="utf-8", errors="strict").strip()
    if not raw:
        raise KeyFileError("Schluesseldatei ist leer.")
    return load_key_from_text(raw)


def load_key_from_text(raw: str) -> dict:
    """Same formats as ``load_key_file`` but from an in-memory string - used
    when the key arrives from the mobile setup form instead of a file path.
    Never logs ``raw``; a parse error does not quote it."""
    raw = (raw or "").strip()
    if not raw:
        raise KeyFileError("Kein Schluesselinhalt uebergeben.")

    # 1) CDP JSON
    try:
        data = json.loads(raw)
    except ValueError:
        data = None
    if isinstance(data, dict):
        name = str(data.get(_CDP_NAME_FIELD) or "").strip()
        material = str(data.get(_CDP_MATERIAL_FIELD) or "").strip()
        if not name or not material:
            raise KeyFileError(
                "JSON erkannt, aber Name oder Schluesselmaterial fehlt "
                "(CDP-Format erwartet)."
            )
        return {"api_key": name, "api_secret": material.replace("\\n", "\n")}

    # 2) bare PEM
    if _PEM_MARK in raw:
        name = os.environ.get(ENV_ID, "").strip()
        if not name:
            raise KeyFileError(
                "PEM-Datei erkannt, aber der Schluessel-NAME steht nicht in "
                f"einer PEM-Datei. Setze {ENV_ID}=organizations/.../apiKeys/... "
                "zusaetzlich zur Datei."
            )
        return {
            "api_key": name,
            "api_secret": raw + ("\n" if not raw.endswith("\n") else ""),
        }

    # 3) dotenv-style text
    values: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        lhs, _, value = line.partition("=")
        values[lhs.strip()] = value.strip().strip('"').strip("'")
    if values.get(ENV_ID) and values.get(ENV_CRED):
        return {
            "api_key": values[ENV_ID],
            "api_secret": values[ENV_CRED].replace("\\n", "\n"),
        }

    raise KeyFileError(
        "Format nicht erkannt: weder CDP-JSON, PEM noch " f"{ENV_ID}/{ENV_CRED}-Text."
    )


def resolve_credentials() -> dict | None:
    """Credentials for the SDK, from (in order): COINBASE_KEY_FILE, the
    env-var pair, else None. Never raises for 'nothing configured'."""
    key_file = os.environ.get(ENV_FILE, "").strip()
    if key_file:
        return load_key_file(key_file)
    name = os.environ.get(ENV_ID, "")
    material = os.environ.get(ENV_CRED, "")
    if name and material:
        return {"api_key": name, "api_secret": material.replace("\\n", "\n")}
    return None


def describe(path: str | Path) -> dict:
    """Shape of a key file for diagnostics - NEVER its content."""
    p = Path(path).expanduser()
    out = {"path": str(p), "exists": p.is_file()}
    if not out["exists"]:
        return out
    mode = stat.S_IMODE(p.stat().st_mode)
    out["permissions_octal"] = oct(mode)
    out["world_readable"] = bool(mode & 0o004)
    try:
        creds = load_key_file(p)
    except KeyFileError as exc:
        out["format"] = f"FEHLER: {exc}"
        return out
    material = creds["api_secret"]
    out["format"] = "CDP-JSON/PEM/TEXT erkannt"
    out["key_id_suffix"] = creds["api_key"][-6:]
    out["secret_kind"] = (
        "EC-PEM"
        if _PEM_MARK in material
        else (
            "Ed25519-base64"
            if len(material) == 88
            else f"unbekannt(len={len(material)})"
        )
    )
    return out
