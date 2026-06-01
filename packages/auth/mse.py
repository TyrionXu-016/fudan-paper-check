from __future__ import annotations

import os

from fastapi import HTTPException

from mse.models import InitiatorRole, ProjectStatus, ReviewStatus, TutoringProject, UserRole
from storage.users import User


def require_role(user: User, *roles: str) -> None:
    role = getattr(user, "role", "advisor")
    if role not in roles:
        raise HTTPException(403, f"role {role} not allowed")


def assert_project_advisor(project: TutoringProject, user: User) -> None:
    if project.advisor_id != user.id:
        raise HTTPException(403, "advisor only")


def assert_project_member(project: TutoringProject, user: User) -> None:
    if project.advisor_id == user.id or project.student_id == user.id:
        return
    raise HTTPException(403, "project member only")


def assert_project_student(project: TutoringProject, user: User) -> None:
    if project.student_id != user.id:
        raise HTTPException(403, "student only")


def assert_round_visible(
    project: TutoringProject, user: User, review_status: ReviewStatus
) -> None:
    if review_status == ReviewStatus.PENDING_RELEASE:
        if project.student_id == user.id:
            raise HTTPException(403, "report not released yet")
        assert_project_advisor(project, user)


def assert_can_create_project(user: User, body_role: str | None = None) -> InitiatorRole:
    role = getattr(user, "role", "advisor")
    if role == UserRole.ADVISOR.value:
        return InitiatorRole.ADVISOR
    if role == UserRole.STUDENT.value:
        return InitiatorRole.STUDENT
    raise HTTPException(403, "invalid role")


def get_repo():
    from storage.db import get_session, init_db
    from storage.mse_repository import MseRepository

    init_db()
    return MseRepository(get_session())
