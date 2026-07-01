from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData(schema=os.getenv("MSE_DB_SCHEMA") or None)


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, default="")
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="advisor")
    created_at: Mapped[str] = mapped_column(String, default="")


class MseProjectORM(Base):
    __tablename__ = "mse_projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    initiator_role: Mapped[str] = mapped_column(String, default="advisor")
    advisor_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    advisor_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    student_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    student_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    rule_base_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String, default="draft")
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    auto_notify_student: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String, default="")
    updated_at: Mapped[str] = mapped_column(String, default="")


class MseSubmissionRoundORM(Base):
    __tablename__ = "mse_submission_rounds"
    __table_args__ = (UniqueConstraint("project_id", "round_number"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("mse_projects.id"), index=True)
    round_number: Mapped[int] = mapped_column(Integer)
    job_id: Mapped[str] = mapped_column(String, index=True)
    review_status: Mapped[str] = mapped_column(String, default="pending")
    issue_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    gate_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    gate_reason: Mapped[str] = mapped_column(Text, default="")
    notify_target: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    diff_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[str] = mapped_column(String, default="")
    analyzed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    released_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class MseIssueORM(Base):
    __tablename__ = "mse_issues"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    round_id: Mapped[str] = mapped_column(String, ForeignKey("mse_submission_rounds.id"), index=True)
    job_id: Mapped[str] = mapped_column(String, index=True)
    fingerprint: Mapped[str] = mapped_column(String, index=True)
    code: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    issue_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String)
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    revision_hint: Mapped[str] = mapped_column(Text, default="")
    rule_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    original_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String, default="")


class MseIssueDismissalORM(Base):
    __tablename__ = "mse_issue_dismissals"
    __table_args__ = (UniqueConstraint("project_id", "fingerprint"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("mse_projects.id"), index=True)
    fingerprint: Mapped[str] = mapped_column(String)
    dismissed_by: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(Text, default="")
    dismissed_at: Mapped[str] = mapped_column(String, default="")


class MseInviteTokenORM(Base):
    __tablename__ = "mse_invite_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("mse_projects.id"), index=True)
    target_role: Mapped[str] = mapped_column(String)
    target_email: Mapped[str] = mapped_column(String)
    expires_at: Mapped[str] = mapped_column(String)
    used_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class MseActivityORM(Base):
    __tablename__ = "mse_activity"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("mse_projects.id"), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String, index=True)


class MseInnovationReviewORM(Base):
    __tablename__ = "mse_innovation_reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, ForeignKey("mse_projects.id"), unique=True, index=True)
    round_id: Mapped[str] = mapped_column(String, ForeignKey("mse_submission_rounds.id"), index=True)
    llm_summary: Mapped[str] = mapped_column(Text, default="")
    novelty_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    comparison_notes: Mapped[str] = mapped_column(Text, default="")
    strengths_json: Mapped[str] = mapped_column(Text, default="[]")
    weaknesses_json: Mapped[str] = mapped_column(Text, default="[]")
    suggested_questions_json: Mapped[str] = mapped_column(Text, default="[]")
    advisor_comment: Mapped[str] = mapped_column(Text, default="")
    advisor_decision: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default="")
