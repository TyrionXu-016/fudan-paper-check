from __future__ import annotations

import logging
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mse.models import InnovationReview, RoundIssueDiff, TutoringProject
from notify.base import Notifier
from notify.console import ConsoleNotifier
from schema.models import Issue

logger = logging.getLogger(__name__)


def _default_notifier() -> Notifier:
    mode = os.getenv("NOTIFIER", "console").lower()
    if mode == "smtp":
        from notify.smtp import SmtpNotifier

        return SmtpNotifier()
    if mode == "webhook":
        from notify.webhook import WebhookNotifier

        return WebhookNotifier()
    return ConsoleNotifier()

TEMPLATES = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES)),
    autoescape=select_autoescape(["html"]),
)


def _render(name: str, **ctx) -> str:
    return _env.get_template(name).render(**ctx)


class NotificationService:
    def __init__(self, notifier: Notifier | None = None) -> None:
        self.notifier = notifier or _default_notifier()
        self.app_base = os.getenv("APP_BASE_URL", "http://localhost:3000")

    async def _safe_send(self, to_email: str, subject: str, html: str) -> bool:
        try:
            await self.notifier.send(to_email, subject, html)
            return True
        except Exception as exc:
            logger.warning("email to %s failed: %s", to_email, exc)
            return False

    async def send_student_issues(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
        issues: list[Issue],
        diff: RoundIssueDiff | None = None,
    ) -> None:
        subject = f"[论文辅导] 第 {round_number} 轮审查意见 — {project.title}"
        html = _render(
            "student_issues.html",
            project=project,
            round_number=round_number,
            issues=issues,
            diff=diff,
            report_url=f"{self.app_base}/mse/projects/{project.id}/rounds/{round_number}",
        )
        await self._safe_send(to_email, subject, html)

    async def send_revision_reminder(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
        due_at,
    ) -> None:
        subject = f"[论文辅导] 第 {round_number} 轮修改即将截止 — {project.title}"
        html = _render(
            "revision_reminder.html",
            project=project,
            round_number=round_number,
            due_at=due_at,
            report_url=f"{self.app_base}/mse/projects/{project.id}/rounds/{round_number}",
        )
        await self._safe_send(to_email, subject, html)

    async def send_advisor_preview_ready(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
    ) -> None:
        subject = f"[论文辅导] 待发布审查报告 — {project.title}"
        html = _render(
            "advisor_preview_ready.html",
            project=project,
            round_number=round_number,
            release_url=f"{self.app_base}/mse/projects/{project.id}/rounds/{round_number}",
        )
        await self._safe_send(to_email, subject, html)

    async def send_advisor_ready(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
    ) -> None:
        subject = f"[论文辅导] {project.title} 论文待终审"
        html = _render(
            "advisor_ready.html",
            project=project,
            round_number=round_number,
            review_url=f"{self.app_base}/mse/projects/{project.id}/review",
        )
        await self._safe_send(to_email, subject, html)

    async def send_parse_failed(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
    ) -> None:
        subject = f"[论文辅导] 解析失败 — {project.title}"
        html = _render(
            "parse_failed.html",
            project=project,
            round_number=round_number,
            retry_url=f"{self.app_base}/mse/projects/{project.id}/submit",
        )
        await self._safe_send(to_email, subject, html)

    async def send_analysis_failed(
        self,
        to_email: str,
        project: TutoringProject,
        round_number: int,
        error: str,
    ) -> None:
        subject = f"[论文辅导] 分析失败 — {project.title}"
        html = _render(
            "analysis_failed.html",
            project=project,
            round_number=round_number,
            error=error,
            retry_url=f"{self.app_base}/mse/projects/{project.id}/submit",
        )
        await self._safe_send(to_email, subject, html)

    async def send_invite_student(
        self, to_email: str, project: TutoringProject, invite_url: str
    ) -> None:
        subject = f"[论文辅导] 邀请参与 — {project.title}"
        html = _render("invite_student.html", project=project, invite_url=invite_url)
        await self._safe_send(to_email, subject, html)

    async def send_invite_advisor(
        self, to_email: str, project: TutoringProject, invite_url: str
    ) -> None:
        subject = f"[论文辅导] 学生邀请您辅导 — {project.title}"
        html = _render("invite_advisor.html", project=project, invite_url=invite_url)
        await self._safe_send(to_email, subject, html)

    async def send_student_innovation_decision(
        self,
        to_email: str,
        project: TutoringProject,
        review: InnovationReview,
    ) -> None:
        labels = {"approve": "通过", "revise": "需修改", "reject": "不予通过"}
        decision = labels.get(review.advisor_decision or "", review.advisor_decision or "")
        subject = f"[论文辅导] 终审结果：{decision} — {project.title}"
        html = _render(
            "student_innovation_decision.html",
            project=project,
            review=review,
            project_url=f"{self.app_base}/mse/projects/{project.id}",
        )
        await self._safe_send(to_email, subject, html)


notification_service = NotificationService()
