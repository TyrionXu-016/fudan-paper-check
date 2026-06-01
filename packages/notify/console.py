from __future__ import annotations

import logging

logger = logging.getLogger("notify.console")


class ConsoleNotifier:
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        *,
        text_body: str = "",
    ) -> None:
        logger.info("EMAIL to=%s subject=%s", to_email, subject)
        print(f"\n=== EMAIL to {to_email} ===\nSubject: {subject}\n{text_body or html_body[:500]}\n")
