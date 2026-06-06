from __future__ import annotations

import os
import re
from urllib.parse import urlparse

import httpx


class WebhookNotifier:
    """Send simple text/markdown notifications to Feishu or WeCom webhooks."""

    def __init__(
        self,
        *,
        url: str | None = None,
        kind: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.url = url or os.getenv("WEBHOOK_URL", "")
        self.kind = (kind or os.getenv("WEBHOOK_KIND", "feishu")).strip().lower()
        self.timeout = timeout or float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "15"))

    def _payload(self, subject: str, html_body: str, text_body: str = "") -> dict:
        text = _strip_html(text_body or html_body)
        if self.kind == "wecom":
            return {
                "msgtype": "markdown",
                "markdown": {"content": f"**{subject}**\n\n{text}"},
            }
        return {
            "msg_type": "text",
            "content": {"text": f"{subject}\n{text}"},
        }

    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        *,
        text_body: str = "",
    ) -> None:
        if not self.url:
            raise RuntimeError("WEBHOOK_URL not configured")
        validation_error = validate_webhook_url(self.url)
        if validation_error:
            raise RuntimeError(validation_error)
        payload = self._payload(subject, html_body, text_body)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url, json=payload)
            response.raise_for_status()


def validate_webhook_url(url: str) -> str:
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"}:
        return "WEBHOOK_URL must be http or https"
    if not parsed.netloc:
        return "WEBHOOK_URL must include a host"
    return ""


def _strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
