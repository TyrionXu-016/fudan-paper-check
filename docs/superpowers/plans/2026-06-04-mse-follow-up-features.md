# MSE Follow-Up Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the remaining local-implementable MSE checklist items after quasi-production acceptance, while isolating items that require user-provided external accounts or sample data.

**Architecture:** Keep API compatibility by extending existing MSE models and routes rather than replacing them. Use existing `LLMClient`, `mse.export`, `notify.service`, and SQLite repository boundaries; add small scripts for scheduled reminders and live acceptance without introducing a new worker system.

**Tech Stack:** FastAPI, SQLAlchemy/SQLite, Pydantic, ReportLab, httpx, pytest, shell acceptance scripts.

---

## Current Remaining Checklist Scope

- M1-0: finish `LLMClient` migration evidence for `ConsistencyChecker`.
- M1-5: CNKI/private thesis integration tests. This requires user-provided PDFs/specs and remains external-data blocked.
- M5-1: annotated PDF export with page anchors and Issue list.
- M5-3: revision deadline reminder cron/script.
- M5-4: Feishu/WeCom notification integration.

## File Structure

- Modify `packages/checks/consistency.py`: accept an injected `LLMClient`-compatible client and avoid direct global-only LLM access.
- Modify `tests/test_mse_review_agent.py` or create `tests/test_consistency_llm_client.py`: prove `ConsistencyChecker` uses `LLMClient` responses and falls back safely.
- Modify `packages/mse/export.py`: generate page anchor sections, issue anchors, and a PDF outline/table structure.
- Modify `tests/test_mse_export.py`: verify exported PDF contains page anchor text and issue/rule references.
- Modify `packages/notify/service.py`: add revision reminder rendering and webhook-compatible send surface.
- Create `packages/notify/webhook.py`: implement Feishu and WeCom webhook notifier payloads using `httpx`.
- Create `packages/notify/templates/revision_reminder.html`: HTML reminder email/webhook body.
- Create `packages/mse/reminders.py`: pure function that scans rounds, computes due windows, sends reminders, and records activity.
- Create `scripts/mse_revision_reminders.py`: cron-friendly entry point.
- Create `tests/test_mse_reminders.py`: verify reminder selection, deduplication, and notification call.
- Create `tests/test_notify_webhook.py`: verify Feishu and WeCom payload shapes without network.
- Modify `.env.example`, `deploy/.env.prod.example`, `README.md`, `deploy/README.md`, and `docs/plans/mse-tutoring-system.md`: document cron/webhook settings and mark completed items.

## Task 1: ConsistencyChecker LLMClient Completion

**Files:**
- Modify: `packages/checks/consistency.py`
- Create: `tests/test_consistency_llm_client.py`
- Modify: `docs/plans/mse-tutoring-system.md`

- [ ] **Step 1: Write failing test**

```python
from checks.consistency import ConsistencyChecker
from schema.models import PaperBlock, PaperDocument


class FakeClient:
    def __init__(self):
        self.calls = []

    def is_available(self):
        return True

    def complete_json(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        return {
            "coverage_gaps": ["缺少结果摘要"],
            "unsupported_claims": [
                {"claim": "结论过强", "reason": "实验不足", "evidence_needed": "补充消融实验"}
            ],
        }


def test_consistency_checker_uses_injected_llm_client():
    doc = PaperDocument(blocks=[
        PaperBlock(type="paragraph", text="摘要：本文提出模型。"),
        PaperBlock(type="paragraph", section="experiment", text="实验部分。"),
        PaperBlock(type="paragraph", section="conclusion", text="结论过强。"),
    ])
    client = FakeClient()

    issues = ConsistencyChecker(client=client).check(doc)

    assert client.calls
    assert {i.code for i in issues} >= {"CONSIST_LLM_COVERAGE", "CONSIST_LLM_CLAIM"}
```

- [ ] **Step 2: Verify red**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_consistency_llm_client.py -q`
Expected: failure because `ConsistencyChecker.__init__` does not accept `client`.

- [ ] **Step 3: Implement minimal client injection**

Update `ConsistencyChecker.__init__` to accept `client: LLMClient | None`, use `client.is_available()` for default enablement, and pass that client into `_llm_check`.

- [ ] **Step 4: Verify green**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_consistency_llm_client.py tests/test_pipeline.py -q`
Expected: all pass.

## Task 2: Annotated Issue PDF Export

**Files:**
- Modify: `packages/mse/export.py`
- Modify: `tests/test_mse_export.py`
- Modify: `apps/api/routes/mse.py` only if a route alias is needed.

- [ ] **Step 1: Write failing test**

Add a test that builds a PDF with two issues on different pages and asserts extracted PDF text contains:

```python
assert "Issue Anchor: page-3" in text
assert "规则 rule-1" in text
assert "原文摘录" in text
```

- [ ] **Step 2: Verify red**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_export.py::test_export_pdf_contains_page_anchors_and_rule_refs -q`
Expected: failure because the PDF currently only contains the table.

- [ ] **Step 3: Implement report anchors**

Add a helper in `packages/mse/export.py` that groups issues by page and appends:

```text
Issue Anchor: page-{page}
问题编号 / 严重级别 / 规范 rule_ref / 原文摘录 / 修改建议
```

Keep existing `export.pdf` route unchanged; this upgrades the returned PDF contents without breaking clients.

- [ ] **Step 4: Verify green**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_export.py -q`
Expected: all pass.

## Task 3: Revision Deadline Reminder Cron

**Files:**
- Create: `packages/mse/reminders.py`
- Create: `scripts/mse_revision_reminders.py`
- Create: `packages/notify/templates/revision_reminder.html`
- Modify: `packages/notify/service.py`
- Create: `tests/test_mse_reminders.py`

- [ ] **Step 1: Write failing test**

Create a SQLite-backed project with a latest round in `issues_found`, set `analyzed_at` to 6 days ago, run `send_revision_reminders(now=day7_minus_12h)`, and assert one notification is sent and one `revision_reminder_sent` activity is recorded.

- [ ] **Step 2: Verify red**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_reminders.py -q`
Expected: import failure because `mse.reminders` does not exist.

- [ ] **Step 3: Implement reminder scan**

Use env defaults:

```text
MSE_REVISION_DUE_DAYS=7
MSE_REVISION_REMINDER_WINDOW_HOURS=24
MSE_REVISION_REMINDER_DRY_RUN=0
```

Send reminders only for latest `issues_found` rounds with a bound student email and no prior `revision_reminder_sent:{round_id}` activity.

- [ ] **Step 4: Verify green**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_reminders.py -q`
Expected: all pass.

## Task 4: Feishu/WeCom Webhook Notifier

**Files:**
- Create: `packages/notify/webhook.py`
- Modify: `packages/notify/service.py`
- Create: `tests/test_notify_webhook.py`
- Modify: `.env.example`, `deploy/.env.prod.example`, `README.md`, `deploy/README.md`

- [ ] **Step 1: Write failing tests**

Test that:

```python
WebhookNotifier(kind="feishu")._payload("subj", "body") == {"msg_type": "text", "content": {"text": "..."}}
WebhookNotifier(kind="wecom")._payload("subj", "body") == {"msgtype": "markdown", "markdown": {"content": "..."}}
```

- [ ] **Step 2: Verify red**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_notify_webhook.py -q`
Expected: import failure because `notify.webhook` does not exist.

- [ ] **Step 3: Implement webhook notifier**

Support:

```text
NOTIFIER=webhook
WEBHOOK_KIND=feishu|wecom
WEBHOOK_URL=https://...
WEBHOOK_TIMEOUT_SECONDS=15
```

Do not log webhook URLs.

- [ ] **Step 4: Verify green**

Run: `PYTHONPATH=packages:apps python3 -m pytest tests/test_notify_webhook.py -q`
Expected: all pass.

## Task 5: Documentation And Acceptance

**Files:**
- Modify: `.env.example`
- Modify: `deploy/.env.prod.example`
- Modify: `README.md`
- Modify: `deploy/README.md`
- Modify: `docs/plans/mse-tutoring-system.md`

- [ ] **Step 1: Update docs**

Document cron:

```bash
MSE_REVISION_DUE_DAYS=7 MSE_REVISION_REMINDER_WINDOW_HOURS=24 \
  PYTHONPATH=packages:apps python3 scripts/mse_revision_reminders.py
```

Document webhook:

```bash
NOTIFIER=webhook
WEBHOOK_KIND=feishu
WEBHOOK_URL=https://...
```

- [ ] **Step 2: Mark checklist**

Mark M1-0, M5-1, M5-3, M5-4 as complete if tests pass. Leave M1-5 unchecked until the user provides CNKI/private samples.

- [ ] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=packages:apps python3 -m pytest tests/test_consistency_llm_client.py tests/test_mse_export.py tests/test_mse_reminders.py tests/test_notify_webhook.py -q
PYTHONPATH=packages:apps python3 -m pytest
```

Expected: all existing tests pass with no new network dependency.

## External Configuration Needed Later

- CNKI/private thesis set for M1-5:
  - 3 CS master thesis PDFs.
  - Matching college thesis specification PDFs/MD.
  - A local manifest describing school, discipline, title, and expected page coverage.
- Live Feishu/WeCom webhook verification:
  - `WEBHOOK_KIND=feishu` or `WEBHOOK_KIND=wecom`.
  - `WEBHOOK_URL`.
  - A test target group where acceptance notifications may be posted.

## Execution Status

- [x] M1-0 `ConsistencyChecker` uses injectable `LLMClient` and is covered by `tests/test_consistency_llm_client.py`.
- [x] M5-1 PDF export includes page anchors, rule references, original excerpts, and revision hints; covered by `tests/test_mse_export.py`.
- [x] M5-3 revision reminder cron entry exists at `scripts/mse_revision_reminders.py`; covered by `tests/test_mse_reminders.py`.
- [x] M5-4 webhook notifier supports Feishu and WeCom payloads; covered by `tests/test_notify_webhook.py` and local E2E `scripts/mse_acceptance_webhook.py`.
- [x] M1-5 input readiness checker exists at `scripts/mse_check_sample_manifest.py`; covered by `tests/test_mse_sample_manifest.py`.
- [x] External configuration status checker exists at `scripts/mse_config_status.py`; it validates quasi-prod env, Dartmouth public PDF identity, private samples, and webhook live config; covered by `tests/test_mse_config_status.py`.
- [x] Dartmouth public PDF manual import helper exists at `scripts/mse_import_public_thesis_pdf.py`; covered by `tests/test_mse_public_thesis_import.py`.
- [x] CNKI/institution private sample import helper exists at `scripts/mse_import_private_sample.py`; covered by `tests/test_mse_private_sample_import.py`.
- [x] Final live aggregate acceptance exists at `scripts/mse_acceptance_final_live.sh`; it preflights full config and runs quasi-prod with private sample + webhook live extras; covered by `tests/test_mse_final_live_script.py`.
- [x] M1-5 live acceptance entrypoint exists at `scripts/mse_acceptance_private_samples.py`; it reports `CONFIG_REQUIRED` until local PDFs/specs are provided under `samples/mse/theses/` and `samples/mse/specs/`.
- [x] Live Feishu/WeCom delivery entrypoint exists at `scripts/mse_acceptance_webhook_live.py`; it reports `CONFIG_REQUIRED` until `WEBHOOK_URL` is configured for a test group, validates URL scheme, and redacts URL secrets on failure.
- [ ] M1-5 live CNKI/private thesis acceptance has not been run successfully because local private PDFs/specs are not present.
- [ ] Live Feishu/WeCom delivery has not been run successfully because `WEBHOOK_URL` is not configured.
