#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import os
import sys

from notify.webhook import WebhookNotifier, validate_webhook_url


async def main() -> int:
    url = os.getenv("WEBHOOK_URL", "").strip()
    kind = os.getenv("WEBHOOK_KIND", "feishu").strip().lower()
    if not url:
        print("CONFIG_REQUIRED: WEBHOOK_URL is not configured")
        print("Set NOTIFIER=webhook WEBHOOK_KIND=feishu|wecom WEBHOOK_URL=...")
        return 2
    if validation_error := validate_webhook_url(url):
        print(f"CONFIG_REQUIRED: {validation_error}")
        return 2
    if kind not in {"feishu", "wecom"}:
        print("CONFIG_REQUIRED: WEBHOOK_KIND must be feishu or wecom")
        return 2

    notifier = WebhookNotifier(kind=kind, url=url)
    try:
        await notifier.send(
            "webhook-live@example.local",
            "MSE webhook live acceptance",
            "<p>这是一条 MSE webhook live 验收通知。</p>",
        )
    except Exception as exc:
        print("FAIL: webhook live acceptance")
        print(f"ERROR_TYPE: {type(exc).__name__}")
        return 1
    print(f"OK: webhook live acceptance sent kind={kind}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
