from __future__ import annotations

from fastapi import HTTPException

from mse.models import ProjectStatus, ReviewStatus, TutoringProject


class ProjectFSMError(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=409, detail=detail)


def assert_both_members_bound(project: TutoringProject) -> None:
    if not project.advisor_id or not project.student_id:
        raise ProjectFSMError("project requires both advisor and student to be bound")
    if not project.rule_base_ids:
        raise ProjectFSMError("project requires at least one rule document before submissions")


def can_submit(project: TutoringProject) -> None:
    if project.status not in (ProjectStatus.ACTIVE, ProjectStatus.ANALYZING):
        if project.status == ProjectStatus.DRAFT:
            assert_both_members_bound(project)
            raise ProjectFSMError("project is not active")
        raise ProjectFSMError(f"cannot submit in status {project.status.value}")


def on_member_bound(project: TutoringProject) -> ProjectStatus:
    if project.advisor_id and project.student_id and project.rule_base_ids:
        return ProjectStatus.ACTIVE
    return ProjectStatus.PENDING_MEMBER if (
        project.advisor_id or project.student_id
    ) else ProjectStatus.DRAFT


def on_submission(project: TutoringProject) -> ProjectStatus:
    can_submit(project)
    return ProjectStatus.ANALYZING


def on_analysis_complete(
    project: TutoringProject,
    *,
    gate_passed: bool,
    pending_release: bool,
) -> tuple[ProjectStatus, ReviewStatus]:
    if pending_release:
        return project.status, ReviewStatus.PENDING_RELEASE
    if gate_passed:
        return ProjectStatus.AWAITING_ADVISOR, ReviewStatus.PASSED
    return ProjectStatus.ACTIVE, ReviewStatus.ISSUES_FOUND


def on_release(project: TutoringProject, gate_passed: bool) -> ProjectStatus:
    if gate_passed:
        return ProjectStatus.AWAITING_ADVISOR
    return ProjectStatus.ACTIVE


def on_parse_failed() -> ReviewStatus:
    return ReviewStatus.PARSE_FAILED


def on_analysis_failed() -> ReviewStatus:
    return ReviewStatus.ANALYSIS_FAILED


def on_advisor_decision(project: TutoringProject, decision: str) -> ProjectStatus:
    if decision == "approve":
        return ProjectStatus.COMPLETED
    if decision in ("revise", "reject"):
        return ProjectStatus.ACTIVE
    raise ProjectFSMError(f"unknown decision {decision}")
