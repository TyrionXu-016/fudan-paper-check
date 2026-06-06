from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from mse.models import ReviewStatus, SubmissionRound
from storage.db import get_session, init_db, reset_engine
from storage.models_orm import MseActivityORM
from storage.mse_repository import MseRepository
from storage.users import User, user_store


class FakeReminderService:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, int, datetime]] = []

    async def send_revision_reminder(
        self,
        to_email: str,
        project,
        round_number: int,
        due_at: datetime,
    ) -> None:
        self.sent.append((to_email, project.title, round_number, due_at))


@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    reset_engine()
    monkeypatch.setenv("MSE_DATABASE_URL", f"sqlite:///{tmp_path / 'mse.db'}")
    init_db()
    yield
    reset_engine()


def _seed_due_round(now: datetime) -> None:
    advisor = User(
        id="advisor-1",
        email="advisor@example.com",
        name="Advisor",
        password_hash="x",
        role="advisor",
    )
    student = User(
        id="student-1",
        email="student@example.com",
        name="Student",
        password_hash="x",
        role="student",
    )
    user_store.save(advisor)
    user_store.save(student)

    session = get_session()
    try:
        repo = MseRepository(session)
        project = repo.create_project(
            title="提醒测试",
            initiator=advisor,
            student_email=student.email,
        )
        repo.bind_member(project.id, student_id=student.id)
        round_obj = repo.create_round(project.id, "job-reminder")
        data = round_obj.model_dump()
        data.update(
            review_status=ReviewStatus.ISSUES_FOUND,
            issue_count=2,
            warning_count=2,
            analyzed_at=(now - timedelta(days=6, hours=12)).isoformat(),
            released_at=(now - timedelta(days=6, hours=12)).isoformat(),
        )
        repo.update_round(
            SubmissionRound(**data)
        )
    finally:
        session.close()


@pytest.mark.asyncio
async def test_revision_reminder_sends_once_inside_due_window(monkeypatch):
    from mse.reminders import send_revision_reminders

    now = datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc)
    _seed_due_round(now)
    service = FakeReminderService()
    monkeypatch.setenv("MSE_REVISION_DUE_DAYS", "7")
    monkeypatch.setenv("MSE_REVISION_REMINDER_WINDOW_HOURS", "24")

    first = await send_revision_reminders(now=now, service=service)
    second = await send_revision_reminders(now=now, service=service)

    assert first["sent"] == 1
    assert second["sent"] == 0
    assert service.sent == [
        (
            "student@example.com",
            "提醒测试",
            1,
            now + timedelta(hours=12),
        )
    ]

    session = get_session()
    try:
        events = (
            session.query(MseActivityORM)
            .filter(MseActivityORM.event.like("revision_reminder_sent:%"))
            .all()
        )
        assert len(events) == 1
    finally:
        session.close()
