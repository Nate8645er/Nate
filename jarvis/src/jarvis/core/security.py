"""Security layer: capability permissions, confirmations, audit log, sandboxing.

Every side-effecting tool declares a *capability* (e.g. ``"desktop.terminal"``,
``"files.delete"``). Before execution the :class:`PermissionManager` evaluates
the policy for that capability:

* ``allow``  - run without asking
* ``ask``    - ask the user through the registered confirmer (GUI dialog,
               voice prompt or API callback); denial raises
               :class:`PermissionDeniedError`
* ``deny``   - always refuse

Policies are persisted to ``permissions.yaml`` in the data directory so the
user's decisions survive restarts.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml

from jarvis.core.config import JarvisConfig
from jarvis.core.errors import PermissionDeniedError
from jarvis.core.logging import get_logger

logger = get_logger("core.security")

Policy = Literal["allow", "ask", "deny"]

# Called with (capability, human-readable description); returns approval.
Confirmer = Callable[[str, str], Awaitable[bool]]


async def _default_confirmer(capability: str, description: str) -> bool:
    """Deny by default when no interactive confirmer is attached (headless safety)."""
    logger.warning(
        "No confirmer attached; denying '%s' (%s). Attach a confirmer or set policy to 'allow'.",
        capability,
        description,
    )
    return False


class PermissionManager:
    """Evaluates and persists capability policies and writes the audit log."""

    def __init__(self, config: JarvisConfig) -> None:
        self._config = config
        self._policy_path = config.resolve_path(config.security.policy_file)
        self._audit_path = config.data_dir / "logs" / "audit.jsonl"
        self._policies: dict[str, Policy] = {}
        self._confirmer: Confirmer = _default_confirmer
        self._lock = asyncio.Lock()
        self._load()

    # -- persistence ---------------------------------------------------------

    def _load(self) -> None:
        if self._policy_path.is_file():
            raw = yaml.safe_load(self._policy_path.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict):
                for cap, pol in raw.items():
                    if pol in ("allow", "ask", "deny"):
                        self._policies[str(cap)] = pol

    def _save(self) -> None:
        self._policy_path.parent.mkdir(parents=True, exist_ok=True)
        self._policy_path.write_text(
            yaml.safe_dump(dict(sorted(self._policies.items()))), encoding="utf-8"
        )

    # -- API -------------------------------------------------------------------

    def set_confirmer(self, confirmer: Confirmer) -> None:
        """Attach the interactive confirmation callback (GUI/voice/API)."""
        self._confirmer = confirmer

    def policy_for(self, capability: str) -> Policy:
        """Return the effective policy: exact match, then prefix match, then default."""
        if capability in self._policies:
            return self._policies[capability]
        parts = capability.split(".")
        while parts:
            parts.pop()
            prefix = ".".join([*parts, "*"]) if parts else "*"
            if prefix in self._policies:
                return self._policies[prefix]
        if capability in self._config.security.confirm_capabilities:
            return "ask"
        return self._config.security.default_policy

    def set_policy(self, capability: str, policy: Policy) -> None:
        self._policies[capability] = policy
        self._save()

    async def check(self, capability: str, description: str) -> None:
        """Raise :class:`PermissionDeniedError` unless the action is approved."""
        policy = self.policy_for(capability)
        if policy == "deny":
            await self._audit(capability, description, "denied-by-policy")
            raise PermissionDeniedError(capability)
        if policy == "ask":
            async with self._lock:  # serialize prompts
                approved = await self._confirmer(capability, description)
            if not approved:
                await self._audit(capability, description, "denied-by-user")
                raise PermissionDeniedError(capability, "The user declined this action")
        await self._audit(capability, description, "allowed")

    async def _audit(self, capability: str, description: str, outcome: str) -> None:
        if not self._config.security.audit_log:
            return
        record = {
            "ts": datetime.now(UTC).isoformat(),
            "capability": capability,
            "description": description,
            "outcome": outcome,
        }
        try:
            self._audit_path.parent.mkdir(parents=True, exist_ok=True)
            with self._audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            logger.exception("Failed to write audit log")


class PythonSandbox:
    """Executes untrusted Python snippets in an isolated subprocess.

    Isolation strategy: fresh interpreter with ``-I`` (isolated mode), empty
    environment, a temporary working directory that is deleted afterwards,
    a hard wall-clock timeout and truncated output. This is process-level
    isolation, not a jail; capabilities that need real containment should run
    inside the Docker deployment.
    """

    def __init__(self, timeout_seconds: float = 30.0, max_output_chars: int = 20_000) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_output_chars = max_output_chars

    async def run(self, code: str) -> dict[str, str | int]:
        """Run *code* and return ``{"stdout", "stderr", "exit_code"}``."""
        workdir = Path(tempfile.mkdtemp(prefix="jarvis-sandbox-"))
        try:
            script = workdir / "snippet.py"
            script.write_text(code, encoding="utf-8")
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-I",
                str(script),
                cwd=str(workdir),
                env={"PYTHONIOENCODING": "utf-8"},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout_seconds
                )
            except TimeoutError:
                proc.kill()
                await proc.wait()
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {self.timeout_seconds}s",
                    "exit_code": -1,
                }
            return {
                "stdout": stdout.decode("utf-8", "replace")[: self.max_output_chars],
                "stderr": stderr.decode("utf-8", "replace")[: self.max_output_chars],
                "exit_code": proc.returncode if proc.returncode is not None else -1,
            }
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
