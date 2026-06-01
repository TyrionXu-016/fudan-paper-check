from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from schema.models import CheckReport, Issue


class UserRole(str, Enum):
    ADVISOR = "advisor"
    STUDENT = "student"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    PENDING_MEMBER = "pending_member"
    ACTIVE = "active"
    ANALYZING = "analyzing"
    AWAITING_ADVISOR = "awaiting_advisor"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    PARSE_FAILED = "parse_failed"
    ANALYZING = "analyzing"
    ANALYSIS_FAILED = "analysis_failed"
    PENDING_RELEASE = "pending_release"
    ISSUES_FOUND = "issues_found"
    PASSED = "passed"
    FAILED = "failed"


class InitiatorRole(str, Enum):
    ADVISOR = "advisor"
    STUDENT = "student"


class TutoringProject(BaseModel):
    id: str
    title: str
    initiator_role: InitiatorRole = InitiatorRole.ADVISOR
    advisor_id: str | None = None
    advisor_email: str | None = None
    student_id: str | None = None
    student_email: str | None = None
    rule_base_ids: list[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.DRAFT
    current_round: int = 0
    auto_notify_student: bool = True
    created_at: str = ""
    updated_at: str = ""


class SubmissionRound(BaseModel):
    id: str
    project_id: str
    round_number: int
    job_id: str
    review_status: ReviewStatus = ReviewStatus.PENDING
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    gate_passed: bool | None = None
    gate_reason: str = ""
    notify_target: str | None = None
    diff_json: dict[str, Any] | None = None
    submitted_at: str = ""
    analyzed_at: str | None = None
    released_at: str | None = None


class IssueDismissal(BaseModel):
    project_id: str
    fingerprint: str
    dismissed_by: str
    reason: str = ""
    dismissed_at: str = ""


class RoundIssueDiff(BaseModel):
    base_round: int
    current_round: int
    fixed: list[Issue] = Field(default_factory=list)
    new: list[Issue] = Field(default_factory=list)
    persistent: list[Issue] = Field(default_factory=list)
    dismissed: list[Issue] = Field(default_factory=list)


class GateDecision(BaseModel):
    round_id: str
    passed: bool
    reason: str
    notify_target: Literal["student", "advisor"] = "student"


class InnovationReview(BaseModel):
    id: str
    project_id: str
    round_id: str
    llm_summary: str = ""
    novelty_score: float | None = None
    comparison_notes: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    advisor_comment: str = ""
    advisor_decision: Literal["approve", "revise", "reject"] | None = None
    reviewed_at: str | None = None
    created_at: str = ""


class MseRoundReport(BaseModel):
    project_id: str
    round_number: int
    round_id: str
    review_status: ReviewStatus
    gate: GateDecision | None = None
    diff: RoundIssueDiff | None = None
    report: CheckReport | None = None
    released: bool = True
    innovation_preview: InnovationReview | None = None


class DashboardTodo(BaseModel):
    type: str
    project_id: str
    title: str
    round_number: int | None = None
    urgency: str = "normal"


class DashboardActivity(BaseModel):
    at: str
    event: str
    project_id: str
    summary: str


class AdvisorDashboardStats(BaseModel):
    total_projects: int = 0
    active: int = 0
    pending_release: int = 0
    awaiting_advisor: int = 0
    parse_failed: int = 0
    completed: int = 0


class StudentDashboardStats(BaseModel):
    my_projects: int = 0
    in_revision: int = 0
    awaiting_advisor: int = 0
    completed: int = 0


class AdvisorDashboard(BaseModel):
    role: Literal["advisor"] = "advisor"
    stats: AdvisorDashboardStats
    todos: list[DashboardTodo] = Field(default_factory=list)
    activity: list[DashboardActivity] = Field(default_factory=list)


class StudentDashboard(BaseModel):
    role: Literal["student"] = "student"
    stats: StudentDashboardStats
    action_required: list[DashboardTodo] = Field(default_factory=list)
    recent: list[DashboardActivity] = Field(default_factory=list)


class MseDashboardResponse(BaseModel):
    advisor: AdvisorDashboard | None = None
    student: StudentDashboard | None = None


class CreateProjectRequest(BaseModel):
    title: str
    student_email: str | None = None
    advisor_email: str | None = None
    auto_notify_student: bool = True


class InviteRequest(BaseModel):
    email: str | None = None
    send_email: bool = True


class AcceptInviteRequest(BaseModel):
    token: str


class RetryRoundRequest(BaseModel):
    action: Literal["retry_parse", "reupload"] = "retry_parse"


class ReleaseRoundRequest(BaseModel):
    pass


class DismissIssueRequest(BaseModel):
    reason: str = ""


class InviteInfoResponse(BaseModel):
    token: str
    project_id: str
    project_title: str
    target_role: str
    target_email: str
    expires_at: str
    used: bool = False
    expired: bool = False


class SubmitInnovationReviewRequest(BaseModel):
    advisor_comment: str = ""
    advisor_decision: Literal["approve", "revise", "reject"]
