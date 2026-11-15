"""Encrypted-at-rest secret storage for the Coinbase key (Phase 20).

The CDP key file content is encrypted with a Fernet key derived from an
operator passphrase (PBKDF2-HMAC-SHA256, 240k iterations, random salt) and
written to ``state/secret.enc``. The passphrase is NEVER stored; without it the
file is useless. The decrypted key lives only in process memory after an
explicit unlock.

On disk (``state/secret.enc``), gitignored:
    {"salt": "<base64>", "token": "<fernet-token>", "created_at": "<iso>",
     "key_id_suffix": "...abc123"}   # suffix only, never the secret

Nothing in this module logs or returns the plaintext secret. ``status()``
reports only whether a secret is stored and unlocked, plus the key-id suffix.
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 240_000


class SecretError(RuntimeError):
    """Encryption/decryption failed. The message never contains the secret."""


def _fernet(passphrase: str, salt: bytes) -> Fernet:
    if not passphrase or len(passphrase) < 8:
        raise SecretError("Passphrase muss mindestens 8 Zeichen haben.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))
    return Fernet(key)


class SecretStore:
    """Owns ``state/secret.enc``. The decrypted key is held only in memory."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._plaintext: str | None = None  # decrypted key content, in RAM

    # ---- disk (ciphertext only) -----------------------------------------

    def is_configured(self) -> bool:
        return self.path.is_file()

    def _meta(self) -> dict:
        try:
            return json.loads(self.path.read_text())
        except (OSError, ValueError):
            return {}

    def store(self, plaintext: str, passphrase: str, key_id_suffix: str = "") -> None:
        """Encrypt and persist. Overwrites any previous secret."""
        salt = os.urandom(16)
        token = _fernet(passphrase, salt).encrypt(plaintext.encode("utf-8"))
        payload = {
            "salt": base64.b64encode(salt).decode(),
            "token": token.decode(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "key_id_suffix": key_id_suffix[-6:],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)
        self._plaintext = plaintext  # already unlocked after setup

    def unlock(self, passphrase: str) -> None:
        """Decrypt the stored secret into memory. Wrong passphrase -> error,
        and the message does not reveal anything about the secret."""
        meta = self._meta()
        if not meta.get("token") or not meta.get("salt"):
            raise SecretError("Kein gespeicherter Schluessel vorhanden.")
        salt = base64.b64decode(meta["salt"])
        try:
            plain = _fernet(passphrase, salt).decrypt(meta["token"].encode())
        except (InvalidToken, ValueError):
            raise SecretError("Passphrase falsch oder Datei beschaedigt.")
        self._plaintext = plain.decode("utf-8")

    def lock(self) -> None:
        """Forget the decrypted key (memory only)."""
        self._plaintext = None

    def clear(self) -> None:
        """Delete the stored secret entirely."""
        self.lock()
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    @property
    def is_unlocked(self) -> bool:
        return self._plaintext is not None

    def plaintext(self) -> str:
        if self._plaintext is None:
            raise SecretError("Schluessel ist nicht entsperrt.")
        return self._plaintext

    def try_env_unlock(self, env_var: str = "HYPERGROK_SECRET_PASSPHRASE") -> bool:
        """For a persistent host: if the passphrase is in the environment,
        unlock automatically at start. The passphrase itself is the host's own
        secret management (e.g. the platform's env-var vault)."""
        pw = os.environ.get(env_var, "")
        if pw and self.is_configured():
            try:
                self.unlock(pw)
                return True
            except SecretError:
                return False
        return False

    def status(self) -> dict:
        meta = self._meta() if self.is_configured() else {}
        return {
            "configured": self.is_configured(),
            "unlocked": self.is_unlocked,
            "key_id_suffix": meta.get("key_id_suffix", ""),
            "created_at": meta.get("created_at", ""),
        }
