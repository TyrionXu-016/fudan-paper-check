from __future__ import annotations

import asyncio
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class SmtpNotifier:
    """Send email via SMTP (TLS). Configure with SMTP_* env vars."""

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_addr = os.getenv("SMTP_FROM", self.user or "noreply@localhost")
        self.use_tls = os.getenv("SMTP_USE_TLS", "1").lower() in ("1", "true", "yes")

    def _send_sync(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
    ) -> None:
        if not self.host:
            raise RuntimeError("SMTP_HOST not configured")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to_email
        plain = text_body or _strip_html(html_body)
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(self.host, self.port, timeout=30) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.user and self.password:
                smtp.login(self.user, self.password)
            smtp.sendmail(self.from_addr, [to_email], msg.as_string())

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        *,
        text_body: str = "",
    ) -> None:
        await asyncio.to_thread(
            self._send_sync, to_email, subject, html_body, text_body
        )


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()
