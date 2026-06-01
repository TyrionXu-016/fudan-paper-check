from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from mse.issue_diff import issue_fingerprint
from mse.models import (
    AdvisorDashboard,
    AdvisorDashboardStats,
    DashboardActivity,
    DashboardTodo,
    InnovationReview,
    InitiatorRole,
    IssueDismissal,
    MseRoundReport,
    ProjectStatus,
    ReviewStatus,
    RoundIssueDiff,
    StudentDashboard,
    StudentDashboardStats,
    SubmissionRound,
    TutoringProject,
    UserRole,
)
from schema.models import CheckReport, Issue, IssueSeverity, IssueType
from storage.models_orm import (
    MseActivityORM,
    MseInviteTokenORM,
    MseInnovationReviewORM,
    MseIssueDismissalORM,
    MseIssueORM,
    MseProjectORM,
    MseSubmissionRoundORM,
)
from storage.users import User, now_iso


def _parse_rule_ids(raw: str) -> list[str]:
    try:
        return json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []


def _project_from_orm(row: MseProjectORM) -> TutoringProject:
    return TutoringProject(
        id=row.id,
        title=row.title,
        initiator_role=InitiatorRole(row.initiator_role),
        advisor_id=row.advisor_id,
        advisor_email=row.advisor_email,
        student_id=row.student_id,
        student_email=row.student_email,
        rule_base_ids=_parse_rule_ids(row.rule_base_ids_json),
        status=ProjectStatus(row.status),
        current_round=row.current_round,
        auto_notify_student=row.auto_notify_student,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _round_from_orm(row: MseSubmissionRoundORM) -> SubmissionRound:
    diff = None
    if row.diff_json:
        try:
            diff = json.loads(row.diff_json)
        except json.JSONDecodeError:
            diff = None
    return SubmissionRound(
        id=row.id,
        project_id=row.project_id,
        round_number=row.round_number,
        job_id=row.job_id,
        review_status=ReviewStatus(row.review_status),
        issue_count=row.issue_count,
        error_count=row.error_count,
        warning_count=row.warning_count,
        gate_passed=row.gate_passed,
        gate_reason=row.gate_reason or "",
        notify_target=row.notify_target,
        diff_json=diff,
        submitted_at=row.submitted_at,
        analyzed_at=row.analyzed_at,
        released_at=row.released_at,
    )


def _issue_from_orm(row: MseIssueORM) -> Issue:
    issue_type = IssueType(row.issue_type) if row.issue_type else None
    from schema.models import CheckCategory

    return Issue(
        id=row.id,
        code=row.code,
        category=CheckCategory(row.category),
        severity=IssueSeverity(row.severity),
        issue_type=issue_type,
        section=row.section,
        line=row.page,
        page=row.page,
        message=row.message,
        suggestion=row.revision_hint,
        revision_hint=row.revision_hint,
        rule_ref=row.rule_ref,
        original_text=row.original_text,
    )


def _innovation_from_orm(row: MseInnovationReviewORM) -> InnovationReview:
    return InnovationReview(
        id=row.id,
        project_id=row.project_id,
        round_id=row.round_id,
        llm_summary=row.llm_summary,
        novelty_score=row.novelty_score,
        comparison_notes=row.comparison_notes,
        strengths=_parse_rule_ids(row.strengths_json),
        weaknesses=_parse_rule_ids(row.weaknesses_json),
        suggested_questions=_parse_rule_ids(row.suggested_questions_json),
        advisor_comment=row.advisor_comment,
        advisor_decision=row.advisor_decision,  # type: ignore[arg-type]
        reviewed_at=row.reviewed_at,
        created_at=row.created_at,
    )


class MseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_project(
        self,
        *,
        title: str,
        initiator: User,
        student_email: str | None = None,
        advisor_email: str | None = None,
        auto_notify_student: bool = True,
    ) -> TutoringProject:
        ts = now_iso()
        project_id = str(uuid.uuid4())
        if initiator.role == UserRole.ADVISOR.value:
            initiator_role = InitiatorRole.ADVISOR
            advisor_id = initiator.id
            student_id = None
        else:
            initiator_role = InitiatorRole.STUDENT
            advisor_id = None
            student_id = initiator.id

        row = MseProjectORM(
            id=project_id,
            title=title,
            initiator_role=initiator_role.value,
            advisor_id=advisor_id,
            advisor_email=advisor_email,
            student_id=student_id,
            student_email=student_email,
            rule_base_ids_json="[]",
            status=ProjectStatus.DRAFT.value,
            current_round=0,
            auto_notify_student=auto_notify_student,
            created_at=ts,
            updated_at=ts,
        )
        self.session.add(row)
        self.log_activity(project_id, initiator.id, "project_created", f"创建项目「{title}」")
        self.session.commit()
        return _project_from_orm(row)

    def get_project(self, project_id: str) -> TutoringProject | None:
        row = self.session.get(MseProjectORM, project_id)
        return _project_from_orm(row) if row else None

    def save_project(self, project: TutoringProject) -> TutoringProject:
        row = self.session.get(MseProjectORM, project.id)
        if not row:
            raise ValueError("project not found")
        row.title = project.title
        row.advisor_id = project.advisor_id
        row.advisor_email = project.advisor_email
        row.student_id = project.student_id
        row.student_email = project.student_email
        row.rule_base_ids_json = json.dumps(project.rule_base_ids, ensure_ascii=False)
        row.status = project.status.value
        row.current_round = project.current_round
        row.auto_notify_student = project.auto_notify_student
        row.updated_at = now_iso()
        self.session.commit()
        return _project_from_orm(row)

    def list_projects_for_user(self, user: User) -> list[TutoringProject]:
        q = self.session.query(MseProjectORM)
        if user.role == UserRole.ADVISOR.value:
            rows = q.filter(MseProjectORM.advisor_id == user.id).all()
        else:
            rows = q.filter(MseProjectORM.student_id == user.id).all()
        return [_project_from_orm(r) for r in rows]

    def add_rule_document(self, project_id: str, rule_id: str) -> TutoringProject:
        project = self.get_project(project_id)
        if not project:
            raise ValueError("project not found")
        if rule_id not in project.rule_base_ids:
            project.rule_base_ids.append(rule_id)
        from mse.fsm import on_member_bound

        project.status = on_member_bound(project)
        return self.save_project(project)

    def bind_member(
        self,
        project_id: str,
        *,
        advisor_id: str | None = None,
        student_id: str | None = None,
    ) -> TutoringProject:
        project = self.get_project(project_id)
        if not project:
            raise ValueError("project not found")
        if advisor_id:
            project.advisor_id = advisor_id
        if student_id:
            project.student_id = student_id
        from mse.fsm import on_member_bound

        project.status = on_member_bound(project)
        return self.save_project(project)

    def create_round(self, project_id: str, job_id: str) -> SubmissionRound:
        project = self.get_project(project_id)
        if not project:
            raise ValueError("project not found")
        round_number = project.current_round + 1
        ts = now_iso()
        round_id = str(uuid.uuid4())
        row = MseSubmissionRoundORM(
            id=round_id,
            project_id=project_id,
            round_number=round_number,
            job_id=job_id,
            review_status=ReviewStatus.PENDING.value,
            submitted_at=ts,
        )
        project.current_round = round_number
        project.status = ProjectStatus.ANALYZING
        project.updated_at = ts
        self.session.add(row)
        self.save_project(project)
        self.log_activity(project_id, None, "round_submitted", f"提交第 {round_number} 轮")
        self.session.commit()
        return _round_from_orm(row)

    def get_round(self, project_id: str, round_number: int) -> SubmissionRound | None:
        row = (
            self.session.query(MseSubmissionRoundORM)
            .filter_by(project_id=project_id, round_number=round_number)
            .first()
        )
        return _round_from_orm(row) if row else None

    def get_round_by_id(self, round_id: str) -> SubmissionRound | None:
        row = self.session.get(MseSubmissionRoundORM, round_id)
        return _round_from_orm(row) if row else None

    def list_rounds(self, project_id: str) -> list[SubmissionRound]:
        rows = (
            self.session.query(MseSubmissionRoundORM)
            .filter_by(project_id=project_id)
            .order_by(MseSubmissionRoundORM.round_number)
            .all()
        )
        return [_round_from_orm(r) for r in rows]

    def update_round(self, round_obj: SubmissionRound) -> SubmissionRound:
        row = self.session.get(MseSubmissionRoundORM, round_obj.id)
        if not row:
            raise ValueError("round not found")
        row.review_status = round_obj.review_status.value
        row.issue_count = round_obj.issue_count
        row.error_count = round_obj.error_count
        row.warning_count = round_obj.warning_count
        row.gate_passed = round_obj.gate_passed
        row.gate_reason = round_obj.gate_reason
        row.notify_target = round_obj.notify_target
        row.diff_json = json.dumps(round_obj.diff_json) if round_obj.diff_json else None
        row.analyzed_at = round_obj.analyzed_at
        row.released_at = round_obj.released_at
        self.session.commit()
        return _round_from_orm(row)

    def save_issues(self, round_id: str, job_id: str, issues: list[Issue]) -> None:
        self.session.query(MseIssueORM).filter_by(round_id=round_id).delete()
        ts = now_iso()
        for issue in issues:
            fp = issue_fingerprint(issue)
            row = MseIssueORM(
                id=issue.id or str(uuid.uuid4()),
                round_id=round_id,
                job_id=job_id,
                fingerprint=fp,
                code=issue.code,
                severity=issue.severity.value,
                issue_type=issue.issue_type.value if issue.issue_type else None,
                category=issue.category.value,
                page=getattr(issue, "page", None) or issue.line,
                section=issue.section,
                message=issue.message,
                revision_hint=getattr(issue, "revision_hint", "") or issue.suggestion,
                rule_ref=getattr(issue, "rule_ref", None),
                original_text=issue.original_text,
                created_at=ts,
            )
            self.session.add(row)
        self.session.commit()

    def list_issues(self, round_id: str) -> list[Issue]:
        rows = (
            self.session.query(MseIssueORM)
            .filter_by(round_id=round_id)
            .order_by(MseIssueORM.page, MseIssueORM.created_at)
            .all()
        )
        return [_issue_from_orm(r) for r in rows]

    def dismiss_issue(
        self, project_id: str, fingerprint: str, advisor_id: str, reason: str = ""
    ) -> IssueDismissal:
        existing = (
            self.session.query(MseIssueDismissalORM)
            .filter_by(project_id=project_id, fingerprint=fingerprint)
            .first()
        )
        ts = now_iso()
        if existing:
            existing.reason = reason
            existing.dismissed_at = ts
        else:
            existing = MseIssueDismissalORM(
                id=str(uuid.uuid4()),
                project_id=project_id,
                fingerprint=fingerprint,
                dismissed_by=advisor_id,
                reason=reason,
                dismissed_at=ts,
            )
            self.session.add(existing)
        self.session.commit()
        return IssueDismissal(
            project_id=project_id,
            fingerprint=fingerprint,
            dismissed_by=advisor_id,
            reason=reason,
            dismissed_at=ts,
        )

    def list_dismissed_fingerprints(self, project_id: str) -> set[str]:
        rows = (
            self.session.query(MseIssueDismissalORM)
            .filter_by(project_id=project_id)
            .all()
        )
        return {r.fingerprint for r in rows}

    def save_invite_token(
        self,
        token: str,
        project_id: str,
        target_role: UserRole,
        target_email: str,
        expires_at: str,
    ) -> None:
        row = MseInviteTokenORM(
            token=token,
            project_id=project_id,
            target_role=target_role.value,
            target_email=target_email.lower(),
            expires_at=expires_at,
        )
        self.session.merge(row)
        self.session.commit()

    def get_invite_token(self, token: str) -> MseInviteTokenORM | None:
        return self.session.get(MseInviteTokenORM, token)

    def mark_invite_used(self, token: str) -> None:
        row = self.get_invite_token(token)
        if row:
            row.used_at = now_iso()
            self.session.commit()

    def log_activity(
        self,
        project_id: str,
        user_id: str | None,
        event: str,
        summary: str,
    ) -> None:
        self.session.add(
            MseActivityORM(
                id=str(uuid.uuid4()),
                project_id=project_id,
                user_id=user_id,
                event=event,
                summary=summary,
                created_at=now_iso(),
            )
        )

    def recent_activity(self, project_ids: list[str], limit: int = 20) -> list[DashboardActivity]:
        if not project_ids:
            return []
        rows = (
            self.session.query(MseActivityORM)
            .filter(MseActivityORM.project_id.in_(project_ids))
            .order_by(MseActivityORM.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            DashboardActivity(
                at=r.created_at,
                event=r.event,
                project_id=r.project_id,
                summary=r.summary,
            )
            for r in rows
        ]

    def build_round_report(
        self,
        project: TutoringProject,
        round_obj: SubmissionRound,
        report: CheckReport | None = None,
        diff: RoundIssueDiff | None = None,
    ) -> MseRoundReport:
        from mse.models import GateDecision

        gate = None
        if round_obj.gate_passed is not None:
            gate = GateDecision(
                round_id=round_obj.id,
                passed=bool(round_obj.gate_passed),
                reason=round_obj.gate_reason,
                notify_target=round_obj.notify_target or "student",
            )
        released = round_obj.review_status not in (
            ReviewStatus.PENDING_RELEASE,
            ReviewStatus.PENDING,
            ReviewStatus.PARSING,
            ReviewStatus.ANALYZING,
        )
        if round_obj.review_status == ReviewStatus.PENDING_RELEASE:
            released = False
        innovation = None
        if round_obj.gate_passed:
            innovation = self.get_innovation_review(project.id)
        return MseRoundReport(
            project_id=project.id,
            round_number=round_obj.round_number,
            round_id=round_obj.id,
            review_status=round_obj.review_status,
            gate=gate,
            diff=diff,
            report=report,
            released=released,
            innovation_preview=innovation,
        )

    def save_innovation_review(self, review: InnovationReview) -> InnovationReview:
        existing = (
            self.session.query(MseInnovationReviewORM)
            .filter_by(project_id=review.project_id)
            .first()
        )
        if existing:
            return _innovation_from_orm(existing)
        row = MseInnovationReviewORM(
            id=review.id,
            project_id=review.project_id,
            round_id=review.round_id,
            llm_summary=review.llm_summary,
            novelty_score=review.novelty_score,
            comparison_notes=review.comparison_notes,
            strengths_json=json.dumps(review.strengths, ensure_ascii=False),
            weaknesses_json=json.dumps(review.weaknesses, ensure_ascii=False),
            suggested_questions_json=json.dumps(review.suggested_questions, ensure_ascii=False),
            advisor_comment=review.advisor_comment,
            advisor_decision=review.advisor_decision,
            reviewed_at=review.reviewed_at,
            created_at=review.created_at or now_iso(),
        )
        self.session.add(row)
        self.session.commit()
        return _innovation_from_orm(row)

    def get_innovation_review(self, project_id: str) -> InnovationReview | None:
        row = (
            self.session.query(MseInnovationReviewORM)
            .filter_by(project_id=project_id)
            .first()
        )
        return _innovation_from_orm(row) if row else None

    def submit_innovation_decision(
        self,
        project_id: str,
        *,
        advisor_id: str,
        comment: str,
        decision: str,
    ) -> InnovationReview:
        row = (
            self.session.query(MseInnovationReviewORM)
            .filter_by(project_id=project_id)
            .first()
        )
        if not row:
            raise ValueError("innovation review not found")
        ts = now_iso()
        row.advisor_comment = comment
        row.advisor_decision = decision
        row.reviewed_at = ts
        self.session.commit()

        project = self.get_project(project_id)
        if project:
            from mse.fsm import on_advisor_decision

            project.status = on_advisor_decision(project, decision)
            self.save_project(project)
        self.log_activity(
            project_id,
            advisor_id,
            "innovation_reviewed",
            f"导师终审：{decision}",
        )
        return _innovation_from_orm(row)

    def advisor_dashboard(self, user_id: str) -> AdvisorDashboard:
        projects = [
            _project_from_orm(r)
            for r in self.session.query(MseProjectORM)
            .filter(MseProjectORM.advisor_id == user_id)
            .all()
        ]
        stats = AdvisorDashboardStats(total_projects=len(projects))
        todos: list[DashboardTodo] = []
        project_ids: list[str] = []

        for p in projects:
            project_ids.append(p.id)
            if p.status == ProjectStatus.COMPLETED:
                stats.completed += 1
            elif p.status == ProjectStatus.AWAITING_ADVISOR:
                stats.awaiting_advisor += 1
                todos.append(
                    DashboardTodo(
                        type="awaiting_innovation",
                        project_id=p.id,
                        title=p.title,
                        urgency="high",
                    )
                )
            elif p.status in (ProjectStatus.ACTIVE, ProjectStatus.ANALYZING):
                stats.active += 1

            latest = (
                self.session.query(MseSubmissionRoundORM)
                .filter_by(project_id=p.id)
                .order_by(MseSubmissionRoundORM.round_number.desc())
                .first()
            )
            if latest:
                if latest.review_status == ReviewStatus.PENDING_RELEASE.value:
                    stats.pending_release += 1
                    todos.append(
                        DashboardTodo(
                            type="pending_release",
                            project_id=p.id,
                            title=p.title,
                            round_number=latest.round_number,
                            urgency="high",
                        )
                    )
                elif latest.review_status == ReviewStatus.PARSE_FAILED.value:
                    stats.parse_failed += 1
                    todos.append(
                        DashboardTodo(
                            type="parse_failed",
                            project_id=p.id,
                            title=p.title,
                            round_number=latest.round_number,
                            urgency="high",
                        )
                    )
            if p.status == ProjectStatus.PENDING_MEMBER and p.initiator_role == InitiatorRole.STUDENT:
                todos.append(
                    DashboardTodo(
                        type="pending_invite_accept",
                        project_id=p.id,
                        title=p.title,
                        urgency="normal",
                    )
                )

        activity = self.recent_activity(project_ids)
        return AdvisorDashboard(stats=stats, todos=todos, activity=activity)

    def student_dashboard(self, user_id: str) -> StudentDashboard:
        projects = [
            _project_from_orm(r)
            for r in self.session.query(MseProjectORM)
            .filter(MseProjectORM.student_id == user_id)
            .all()
        ]
        stats = StudentDashboardStats(my_projects=len(projects))
        action_required: list[DashboardTodo] = []
        recent: list[DashboardActivity] = []
        project_ids: list[str] = []

        for p in projects:
            project_ids.append(p.id)
            if p.status == ProjectStatus.COMPLETED:
                stats.completed += 1
            elif p.status == ProjectStatus.AWAITING_ADVISOR:
                stats.awaiting_advisor += 1
            elif p.status in (ProjectStatus.ACTIVE, ProjectStatus.ANALYZING):
                stats.in_revision += 1

            latest = (
                self.session.query(MseSubmissionRoundORM)
                .filter_by(project_id=p.id)
                .order_by(MseSubmissionRoundORM.round_number.desc())
                .first()
            )
            if latest:
                if latest.review_status == ReviewStatus.ISSUES_FOUND.value:
                    action_required.append(
                        DashboardTodo(
                            type="in_revision",
                            project_id=p.id,
                            title=p.title,
                            round_number=latest.round_number,
                            urgency="high",
                        )
                    )
                elif latest.review_status == ReviewStatus.PARSE_FAILED.value:
                    action_required.append(
                        DashboardTodo(
                            type="parse_failed",
                            project_id=p.id,
                            title=p.title,
                            round_number=latest.round_number,
                            urgency="high",
                        )
                    )
                recent.append(
                    DashboardActivity(
                        at=latest.submitted_at,
                        event=latest.review_status,
                        project_id=p.id,
                        summary=f"第 {latest.round_number} 轮 · {latest.issue_count} 项问题",
                    )
                )

        activity = self.recent_activity(project_ids, limit=10)
        return StudentDashboard(
            stats=stats,
            action_required=action_required,
            recent=activity or recent,
        )
