from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    async def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        *,
        text_body: str = "",
    ) -> None: ...
