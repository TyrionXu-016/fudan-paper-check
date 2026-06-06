#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class CaptureHandler(BaseHTTPRequestHandler):
    payloads: list[dict] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {"raw": body.decode("utf-8", errors="replace")}
        CaptureHandler.payloads.append(payload)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format: str, *args) -> None:
        return


async def _send(kind: str, url: str) -> None:
    os.environ["NOTIFIER"] = "webhook"
    os.environ["WEBHOOK_KIND"] = kind
    os.environ["WEBHOOK_URL"] = url
    from notify.webhook import WebhookNotifier

    notifier = WebhookNotifier(kind=kind, url=url)
    await notifier.send("student@example.com", "Webhook验收", "<p>本地 webhook 验收</p>")


def _assert_payload(kind: str, payload: dict) -> None:
    if kind == "wecom":
        assert payload.get("msgtype") == "markdown", payload
        assert "Webhook验收" in (payload.get("markdown") or {}).get("content", "")
    else:
        assert payload.get("msg_type") == "text", payload
        assert "Webhook验收" in (payload.get("content") or {}).get("text", "")


def main() -> int:
    server = HTTPServer(("127.0.0.1", 0), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/webhook"
    try:
        for kind in ("feishu", "wecom"):
            before = len(CaptureHandler.payloads)
            asyncio.run(_send(kind, url))
            received = CaptureHandler.payloads[before:]
            if len(received) != 1:
                raise AssertionError(f"{kind} expected 1 payload, got {len(received)}")
            _assert_payload(kind, received[0])
            print(f"OK: {kind} webhook local acceptance")
        return 0
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
