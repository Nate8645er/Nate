"""Email integration over plain SMTP (send) and IMAP (read).

Uses only the standard library (``smtplib``, ``imaplib``, ``email``), running
the blocking protocol calls in worker threads via :func:`asyncio.to_thread`.

Environment variables:

* ``EMAIL_SMTP_HOST`` -- SMTP server host (enables ``email_send``).
* ``EMAIL_SMTP_PORT`` -- SMTP port, default ``587`` (STARTTLS is used when
  the server offers it).
* ``EMAIL_SMTP_USER`` / ``EMAIL_SMTP_PASSWORD`` -- credentials for SMTP
  login and IMAP login (shared between both protocols).
* ``EMAIL_FROM`` -- sender address; defaults to ``EMAIL_SMTP_USER``.
* ``EMAIL_IMAP_HOST`` -- IMAP server host (SSL, port 993; enables
  ``email_list_inbox`` and ``email_read``).
"""

from __future__ import annotations

import asyncio
import email
import email.policy
import imaplib
import smtplib
from email.message import EmailMessage
from typing import Any, Self

from jarvis.core.errors import IntegrationError
from jarvis.integrations.base import IntegrationClient, env, truncate


class EmailClient(IntegrationClient):
    """SMTP send + IMAP inbox reading client (see module docstring for env vars)."""

    service = "email"

    def __init__(
        self,
        *,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        sender: str | None = None,
        imap_host: str | None = None,
    ) -> None:
        super().__init__()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port or 587
        self.user = user
        self.password = password
        self.sender = sender or user
        self.imap_host = imap_host

    @classmethod
    def from_env(cls) -> Self | None:
        smtp_host = env("EMAIL_SMTP_HOST")
        imap_host = env("EMAIL_IMAP_HOST")
        if smtp_host is None and imap_host is None:
            return None
        port_raw = env("EMAIL_SMTP_PORT")
        return cls(
            smtp_host=smtp_host,
            smtp_port=int(port_raw) if port_raw and port_raw.isdigit() else None,
            user=env("EMAIL_SMTP_USER"),
            password=env("EMAIL_SMTP_PASSWORD"),
            sender=env("EMAIL_FROM"),
            imap_host=imap_host,
        )

    # -- SMTP ----------------------------------------------------------------

    async def send(self, to: str, subject: str, body: str) -> dict[str, Any]:
        """Send a plain-text email and report the recipient."""
        if not self.smtp_host:
            raise IntegrationError("email: EMAIL_SMTP_HOST is not configured")
        if not self.sender:
            raise IntegrationError("email: set EMAIL_FROM or EMAIL_SMTP_USER as sender")
        await asyncio.to_thread(self._send_sync, to, subject, body)
        return {"sent": True, "to": to, "subject": subject}

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as smtp:
                smtp.ehlo()
                if smtp.has_extn("starttls"):
                    smtp.starttls()
                    smtp.ehlo()
                if self.user and self.password:
                    smtp.login(self.user, self.password)
                smtp.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise IntegrationError(f"email: SMTP send failed: {exc}", cause=exc) from exc

    # -- IMAP ------------------------------------------------------------------

    async def list_inbox(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return headers of the latest *limit* inbox messages (newest first)."""
        return await asyncio.to_thread(self._list_sync, max(1, min(int(limit), 50)))

    async def read(self, message_id: str) -> dict[str, Any]:
        """Return subject/from/date and the text body of one inbox message.

        *message_id* is the id returned by :meth:`list_inbox`.
        """
        return await asyncio.to_thread(self._read_sync, str(message_id))

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        if not self.imap_host:
            raise IntegrationError("email: EMAIL_IMAP_HOST is not configured")
        try:
            imap = imaplib.IMAP4_SSL(self.imap_host)
            if self.user and self.password:
                imap.login(self.user, self.password)
            imap.select("INBOX", readonly=True)
            return imap
        except (imaplib.IMAP4.error, OSError) as exc:
            raise IntegrationError(f"email: IMAP connect failed: {exc}", cause=exc) from exc

    def _list_sync(self, limit: int) -> list[dict[str, Any]]:
        try:
            with self._connect_imap() as imap:
                _, data = imap.search(None, "ALL")
                ids = data[0].split() if data and data[0] else []
                results: list[dict[str, Any]] = []
                for msg_id in reversed(ids[-limit:]):
                    _, fetched = imap.fetch(msg_id, "(RFC822.HEADER)")
                    raw = _fetch_payload(fetched)
                    if raw is None:
                        continue
                    parsed = email.message_from_bytes(raw, policy=email.policy.default)
                    results.append(
                        {
                            "id": msg_id.decode("ascii"),
                            "subject": str(parsed.get("Subject", "")),
                            "from": str(parsed.get("From", "")),
                            "date": str(parsed.get("Date", "")),
                        }
                    )
                return results
        except imaplib.IMAP4.error as exc:
            raise IntegrationError(f"email: IMAP list failed: {exc}", cause=exc) from exc

    def _read_sync(self, message_id: str) -> dict[str, Any]:
        try:
            with self._connect_imap() as imap:
                _, fetched = imap.fetch(message_id.encode("ascii"), "(RFC822)")
                raw = _fetch_payload(fetched)
                if raw is None:
                    raise IntegrationError(f"email: message '{message_id}' not found")
                parsed = email.message_from_bytes(raw, policy=email.policy.default)
                body = parsed.get_body(preferencelist=("plain",))
                text = body.get_content() if body is not None else ""
                return {
                    "id": message_id,
                    "subject": str(parsed.get("Subject", "")),
                    "from": str(parsed.get("From", "")),
                    "date": str(parsed.get("Date", "")),
                    "body": truncate(text),
                }
        except imaplib.IMAP4.error as exc:
            raise IntegrationError(f"email: IMAP read failed: {exc}", cause=exc) from exc

    # -- tools -----------------------------------------------------------------

    def register_tools(self, app: Any) -> None:
        if self.smtp_host:
            self._register_tool(
                app,
                name="email_send",
                description="Send a plain-text email via the configured SMTP account.",
                handler=self.send,
                parameters={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient address"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["to", "subject", "body"],
                },
                capability="integrations.send",
            )
        if self.imap_host:
            self._register_tool(
                app,
                name="email_list_inbox",
                description="List subject/from/date of the latest emails in the inbox.",
                handler=self.list_inbox,
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                },
            )
            self._register_tool(
                app,
                name="email_read",
                description="Read one email (text body) by the id from email_list_inbox.",
                handler=self.read,
                parameters={
                    "type": "object",
                    "properties": {"message_id": {"type": "string"}},
                    "required": ["message_id"],
                },
            )


def _fetch_payload(fetched: Any) -> bytes | None:
    """Extract the raw message bytes from an ``imap.fetch`` response."""
    for part in fetched or []:
        if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], bytes):
            return part[1]
    return None
