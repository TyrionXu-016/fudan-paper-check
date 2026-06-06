from __future__ import annotations

from notify.webhook import WebhookNotifier


def test_feishu_webhook_payload_uses_text_message() -> None:
    payload = WebhookNotifier(url="https://example.invalid/hook", kind="feishu")._payload(
        "提醒",
        "<p>请查看报告</p>",
    )

    assert payload == {
        "msg_type": "text",
        "content": {"text": "提醒\n请查看报告"},
    }


def test_wecom_webhook_payload_uses_markdown_message() -> None:
    payload = WebhookNotifier(url="https://example.invalid/hook", kind="wecom")._payload(
        "提醒",
        "<p>请查看报告</p>",
    )

    assert payload == {
        "msgtype": "markdown",
        "markdown": {"content": "**提醒**\n\n请查看报告"},
    }
