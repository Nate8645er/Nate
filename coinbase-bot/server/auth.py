"""Authentication for the HyperGrok dashboard — standard library only.

  * Users live in state/users.json (gitignored). Passwords are stored as
    PBKDF2-HMAC-SHA256 with a per-user salt and 240k iterations, never plain.
  * Login returns an opaque session token with an expiry. Sessions are held in
    memory, so a backend restart logs everyone out (deliberate).
  * Roles: "admin" may change state (mode, meetings, emergency stop);
    "viewer" may only read.
  * Brute force: per-username and per-IP attempt counters with a lockout.
  * Every security-relevant action is appended to an audit log.
  * CSRF: state-changing requests must echo the session's CSRF token in a
    header, which a cross-site form cannot do.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
USERS_FILE = STATE / "users.json"
AUDIT_FILE = STATE / "audit.jsonl"

ITERATIONS = 240_000
SESSION_TTL = 12 * 3600
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300


def hash_password(password: str, salt: Optional[bytes] = None) -> dict:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return {"salt": salt.hex(), "hash": digest.hex(), "iterations": ITERATIONS}


def verify_password(password: str, record: dict) -> bool:
    try:
        salt = bytes.fromhex(record["salt"])
        expected = bytes.fromhex(record["hash"])
        iterations = int(record.get("iterations", ITERATIONS))
    except (KeyError, ValueError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(digest, expected)


@dataclass
class Session:
    token: str
    username: str
    role: str
    csrf: str
    expires_at: float

    def alive(self) -> bool:
        return time.time() < self.expires_at


@dataclass
class AuthStore:
    users: dict = field(default_factory=dict)
    sessions: dict = field(default_factory=dict)
    attempts: dict = field(default_factory=dict)   # key -> (count, first_ts)

    # ---- persistence -----------------------------------------------------

    @classmethod
    def load(cls) -> "AuthStore":
        store = cls()
        if USERS_FILE.exists():
            try:
                store.users = json.loads(USERS_FILE.read_text())
            except json.JSONDecodeError:
                store.users = {}
        return store

    def save(self) -> None:
        STATE.mkdir(parents=True, exist_ok=True)
        USERS_FILE.write_text(json.dumps(self.users, indent=2))
        try:
            os.chmod(USERS_FILE, 0o600)
        except OSError:
            pass

    def audit(self, event: str, **data) -> None:
        STATE.mkdir(parents=True, exist_ok=True)
        entry = {"ts": time.time(), "event": event, **data}
        with AUDIT_FILE.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")

    # ---- users -----------------------------------------------------------

    def add_user(self, username: str, password: str, role: str = "viewer") -> None:
        if role not in ("admin", "viewer"):
            raise ValueError("role must be admin or viewer")
        self.users[username] = {"role": role, **hash_password(password)}
        self.save()
        self.audit("user_created", username=username, role=role)

    def bootstrap_admin(self) -> Optional[str]:
        """Create an admin on first start and return the generated password
        once, so it can be printed to the server console (never stored)."""
        if self.users:
            return None
        password = secrets.token_urlsafe(18)
        self.add_user("admin", password, role="admin")
        return password

    # ---- brute force -----------------------------------------------------

    def _locked(self, key: str) -> bool:
        entry = self.attempts.get(key)
        if not entry:
            return False
        count, first = entry
        if time.time() - first > LOCKOUT_SECONDS:
            self.attempts.pop(key, None)
            return False
        return count >= MAX_ATTEMPTS

    def _record_failure(self, key: str) -> None:
        count, first = self.attempts.get(key, (0, time.time()))
        if time.time() - first > LOCKOUT_SECONDS:
            count, first = 0, time.time()
        self.attempts[key] = (count + 1, first)

    # ---- login -----------------------------------------------------------

    def login(self, username: str, password: str, ip: str = "-") -> Optional[Session]:
        for key in (f"u:{username}", f"ip:{ip}"):
            if self._locked(key):
                self.audit("login_locked", username=username, ip=ip)
                return None
        record = self.users.get(username)
        # Always run a hash so a missing user costs the same time as a wrong one.
        ok = verify_password(password, record) if record else verify_password(password, hash_password("x"))
        if not record or not ok:
            self._record_failure(f"u:{username}")
            self._record_failure(f"ip:{ip}")
            self.audit("login_failed", username=username, ip=ip)
            return None
        self.attempts.pop(f"u:{username}", None)
        self.attempts.pop(f"ip:{ip}", None)
        session = Session(secrets.token_urlsafe(32), username, record["role"],
                          secrets.token_urlsafe(16), time.time() + SESSION_TTL)
        self.sessions[session.token] = session
        self.audit("login_ok", username=username, ip=ip, role=record["role"])
        return session

    def logout(self, token: str) -> None:
        session = self.sessions.pop(token, None)
        if session:
            self.audit("logout", username=session.username)

    def session(self, token: str) -> Optional[Session]:
        session = self.sessions.get(token)
        if not session:
            return None
        if not session.alive():
            self.sessions.pop(token, None)
            self.audit("session_expired", username=session.username)
            return None
        return session
