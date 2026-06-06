from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from mse.models import ReviewStatus
from notify.service import notification_service
from storage.db import get_session, init_db
from storage.models_orm import MseActivityORM, MseProjectORM, MseSubmissionRoundORM
from storage.mse_repository import MseRepository
from storage.users import user_store


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return int(raw)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _student_email(project) -> str | None:
    if project.student_id:
        user = user_store.get(project.student_id)
        if user and user.email:
            return user.email
    return project.student_email


async def send_revision_reminders(
    *,
    now: datetime | None = None,
    service: Any = notification_service,
    due_days: int | None = None,
    window_hours: int | None = None,
    dry_run: bool | None = None,
) -> dict[str, int]:
    """Send one reminder for latest rounds whose revision deadline is near."""

    init_db()
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    due_days = due_days if due_days is not None else _env_int("MSE_REVISION_DUE_DAYS", 7)
    window_hours = (
        window_hours
        if window_hours is not None
        else _env_int("MSE_REVISION_REMINDER_WINDOW_HOURS", 24)
    )
    if dry_run is None:
        dry_run = os.getenv("MSE_REVISION_REMINDER_DRY_RUN", "0").lower() in (
            "1",
            "true",
            "yes",
        )

    session = get_session()
    scanned = due = sent = skipped = 0
    try:
        repo = MseRepository(session)
        rows = (
            session.query(MseSubmissionRoundORM)
            .filter(MseSubmissionRoundORM.review_status == ReviewStatus.ISSUES_FOUND.value)
            .order_by(MseSubmissionRoundORM.submitted_at.asc())
            .all()
        )
        for row in rows:
            scanned += 1
            project_row = session.get(MseProjectORM, row.project_id)
            if not project_row or project_row.current_round != row.round_number:
                skipped += 1
                continue

            base = _parse_dt(row.released_at) or _parse_dt(row.analyzed_at)
            if base is None:
                skipped += 1
                continue
            due_at = base + timedelta(days=due_days)
            seconds_until_due = (due_at - now).total_seconds()
            if seconds_until_due < 0 or seconds_until_due > window_hours * 3600:
                skipped += 1
                continue

            event = f"revision_reminder_sent:{row.id}"
            existing = (
                session.query(MseActivityORM)
                .filter_by(project_id=row.project_id, event=event)
                .first()
            )
            if existing:
                skipped += 1
                continue

            project = repo.get_project(row.project_id)
            if not project:
                skipped += 1
                continue
            email = _student_email(project)
            if not email:
                skipped += 1
                continue

            due += 1
            if not dry_run:
                await service.send_revision_reminder(
                    email,
                    project,
                    row.round_number,
                    due_at,
                )
                repo.log_activity(
                    row.project_id,
                    None,
                    event,
                    f"第 {row.round_number} 轮修改截止提醒已发送，截止时间 {due_at.isoformat()}",
                )
                session.commit()
                sent += 1

        return {"scanned": scanned, "due": due, "sent": sent, "skipped": skipped}
    finally:
        session.close()
