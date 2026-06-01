from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from auth.mse import (
    assert_project_advisor,
    assert_project_member,
    assert_project_student,
    assert_round_visible,
    get_repo,
    require_role,
    resolve_invite_for_submit,
)
from auth.service import get_current_user, get_optional_user, get_or_create_student
from mse.invite import generate_invite_token, invite_target_for_project
from mse.rule_bootstrap import bootstrap_project_default_rules
from mse.issue_diff import diff_rounds
from mse.models import (
    AcceptInviteRequest,
    CreateProjectRequest,
    DismissIssueRequest,
    InitiatorRole,
    InnovationReview,
    InviteInfoResponse,
    InviteRequest,
    MseDashboardResponse,
    MseRoundReport,
    ProjectStatus,
    ReleaseRoundRequest,
    RetryRoundRequest,
    ReviewStatus,
    RoundIssueDiff,
    SubmissionRound,
    SubmitInnovationReviewRequest,
    TutoringProject,
    UserRole,
)
from notify.service import notification_service
from schema.models import JobRecord, JobStatus
from storage.jobs import UPLOADS, job_store, now_iso
from storage.users import User, user_store

router = APIRouter(prefix="/v1/mse", tags=["mse"])

MSE_ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".webp", ".zip"}


async def _enqueue_mse_round(project_id: str, round_id: str) -> None:
    if os.getenv("JOB_RUN_INLINE", "").lower() in ("1", "true", "yes"):
        from worker.mse_tasks import process_mse_round

        await process_mse_round({}, project_id, round_id)
        return
    try:
        from arq import create_pool
        from worker.tasks import _build_redis_settings

        redis = await create_pool(_build_redis_settings())
        await redis.enqueue_job("process_mse_round", project_id, round_id)
    except Exception:
        from worker.mse_tasks import process_mse_round

        await process_mse_round({}, project_id, round_id)


@router.get("/dashboard", response_model=MseDashboardResponse)
async def get_dashboard(user: User = Depends(get_current_user)):
    repo = get_repo()
    role = getattr(user, "role", "advisor")
    resp = MseDashboardResponse()
    if role == UserRole.ADVISOR.value:
        resp.advisor = repo.advisor_dashboard(user.id)
    else:
        resp.student = repo.student_dashboard(user.id)
    return resp


@router.post("/projects", response_model=TutoringProject)
async def create_project(body: CreateProjectRequest, user: User = Depends(get_current_user)):
    role = getattr(user, "role", "advisor")
    if role == UserRole.ADVISOR.value:
        if not body.student_email:
            raise HTTPException(400, "student_email required for advisor-initiated project")
        repo = get_repo()
        project = repo.create_project(
            title=body.title,
            initiator=user,
            student_email=body.student_email,
            auto_notify_student=body.auto_notify_student,
        )
        return bootstrap_project_default_rules(project.id, repo)
    if role == UserRole.STUDENT.value:
        if not body.advisor_email:
            raise HTTPException(400, "advisor_email required for student-initiated project")
        repo = get_repo()
        project = repo.create_project(
            title=body.title,
            initiator=user,
            advisor_email=body.advisor_email,
            auto_notify_student=body.auto_notify_student,
        )
        return bootstrap_project_default_rules(project.id, repo)
    raise HTTPException(403, "invalid role")


@router.get("/projects", response_model=list[TutoringProject])
async def list_projects(user: User = Depends(get_current_user)):
    repo = get_repo()
    return repo.list_projects_for_user(user)


@router.get("/projects/{project_id}", response_model=TutoringProject)
async def get_project(project_id: str, user: User = Depends(get_current_user)):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    return project


@router.post("/projects/{project_id}/rules", response_model=TutoringProject)
async def upload_rules(
    project_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    from mse.rule_converter import MAX_RULE_BYTES, RULE_ALLOWED_SUFFIXES, convert_rule_to_markdown
    from rag.mse_rule_index import load_project_index, project_sources_dir, rebuild_project_index_from_sources

    require_role(user, UserRole.ADVISOR.value)
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_advisor(project, user)

    content = await file.read()
    if len(content) > MAX_RULE_BYTES:
        raise HTTPException(400, f"file too large (max {MAX_RULE_BYTES // (1024 * 1024)}MB)")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in RULE_ALLOWED_SUFFIXES:
        raise HTTPException(400, f"unsupported rule file type: {suffix}")

    rule_id = f"rule-{uuid.uuid4().hex[:8]}"
    sources_dir = project_sources_dir(project_id)
    sources_dir.mkdir(parents=True, exist_ok=True)
    orig_path = sources_dir / f"{rule_id}{suffix}"
    orig_path.write_bytes(content)
    md_path = sources_dir / f"{rule_id}.md"
    try:
        convert_rule_to_markdown(orig_path, md_path)
    except (ValueError, RuntimeError) as exc:
        orig_path.unlink(missing_ok=True)
        md_path.unlink(missing_ok=True)
        raise HTTPException(400, str(exc)) from exc

    rebuild_project_index_from_sources(project_id)
    index = load_project_index(project_id)
    if not index or index.get("chunk_count", 0) == 0:
        orig_path.unlink(missing_ok=True)
        md_path.unlink(missing_ok=True)
        raise HTTPException(400, "rule document produced no indexable content")

    return repo.add_rule_document(project_id, rule_id)


@router.post("/projects/{project_id}/rules/default", response_model=TutoringProject)
async def index_default_rules(
    project_id: str,
    user: User = Depends(get_current_user),
):
    require_role(user, UserRole.ADVISOR.value)
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_advisor(project, user)
    from rag.mse_rule_index import build_project_index

    build_project_index(project_id, include_default=True)
    if project.rule_base_ids:
        return project
    return bootstrap_project_default_rules(project_id, repo)


@router.post("/projects/{project_id}/invite")
async def invite_member(
    project_id: str,
    body: InviteRequest | None = None,
    user: User = Depends(get_current_user),
):
    body = body or InviteRequest()
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)

    target = invite_target_for_project(
        project.initiator_role,
        has_advisor=bool(project.advisor_id),
        has_student=bool(project.student_id),
    )
    if not target:
        raise HTTPException(400, "project already has both members")

    if target == UserRole.STUDENT:
        email = body.email or project.student_email
        if not email:
            raise HTTPException(400, "student email required")
    else:
        email = body.email or project.advisor_email
        if not email:
            raise HTTPException(400, "advisor email required")

    token, expires = generate_invite_token(project_id, target, email)
    repo.save_invite_token(token, project_id, target, email, expires)
    invite_url = f"{os.getenv('APP_BASE_URL', 'http://localhost:3000')}/mse/invite/{token}"

    if body.send_email:
        if target == UserRole.STUDENT:
            await notification_service.send_invite_student(email, project, invite_url)
        else:
            await notification_service.send_invite_advisor(email, project, invite_url)

    return {"token": token, "invite_url": invite_url, "target_role": target.value, "expires_at": expires}


@router.get("/invites/{token}", response_model=InviteInfoResponse)
async def get_invite(token: str):
    from datetime import datetime, timezone

    repo = get_repo()
    invite = repo.get_invite_token(token)
    if not invite:
        raise HTTPException(404, "invite not found")
    project = repo.get_project(invite.project_id)
    if not project:
        raise HTTPException(404, "project not found")
    expired = False
    try:
        exp = datetime.fromisoformat(invite.expires_at)
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        expired = datetime.now(timezone.utc) > exp
    except ValueError:
        expired = True
    return InviteInfoResponse(
        token=token,
        project_id=invite.project_id,
        project_title=project.title,
        target_role=invite.target_role,
        target_email=invite.target_email,
        expires_at=invite.expires_at,
        used=bool(invite.used_at),
        expired=expired,
    )


@router.post("/invites/{token}/accept", response_model=TutoringProject)
async def accept_invite_by_token(
    token: str,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    invite = repo.get_invite_token(token)
    if not invite:
        raise HTTPException(404, "invite not found")
    return await accept_invite(
        invite.project_id,
        AcceptInviteRequest(token=token),
        user,
    )


@router.post("/projects/{project_id}/accept", response_model=TutoringProject)
async def accept_invite(
    project_id: str,
    body: AcceptInviteRequest,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")

    invite = repo.get_invite_token(body.token)
    if not invite or invite.project_id != project_id:
        raise HTTPException(400, "invalid invite token")
    if invite.used_at:
        raise HTTPException(400, "invite already used")
    if invite.target_email.lower() != user.email.lower():
        raise HTTPException(403, "email mismatch")
    if invite.target_role != getattr(user, "role", ""):
        raise HTTPException(403, "role mismatch")

    if invite.target_role == UserRole.ADVISOR.value:
        project = repo.bind_member(project_id, advisor_id=user.id)
    else:
        project = repo.bind_member(project_id, student_id=user.id)
    repo.mark_invite_used(body.token)
    repo.log_activity(project_id, user.id, "invite_accepted", f"{user.email} 接受邀请")
    return project


async def _create_submission(
    project_id: str,
    file: UploadFile,
    *,
    user: User | None,
) -> dict:
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")

    from mse.fsm import can_submit

    can_submit(project)

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in MSE_ALLOWED_SUFFIXES:
        raise HTTPException(400, f"unsupported file type: {suffix}")

    job_id = str(uuid.uuid4())
    out_dir = UPLOADS / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / (file.filename or "upload.pdf")
    content = await file.read()
    dest.write_bytes(content)

    record = JobRecord(
        job_id=job_id,
        status=JobStatus.QUEUED,
        user_id=user.id if user else None,
        filename=dest.name,
        journal_profile="generic",
        created_at=now_iso(),
        updated_at=now_iso(),
    )
    job_store.save(record)

    round_obj = repo.create_round(project_id, job_id)
    await _enqueue_mse_round(project_id, round_obj.id)
    return {
        "round_id": round_obj.id,
        "round_number": round_obj.round_number,
        "job_id": job_id,
    }


@router.post("/invites/{token}/submissions")
async def submit_via_invite(token: str, file: UploadFile = File(...)):
    repo = get_repo()
    invite = resolve_invite_for_submit(repo, token)
    project = repo.get_project(invite.project_id)
    if not project:
        raise HTTPException(404, "project not found")

    student = get_or_create_student(invite.target_email)
    if not project.student_id:
        repo.bind_member(invite.project_id, student_id=student.id)
        repo.mark_invite_used(token)
        repo.log_activity(
            invite.project_id,
            student.id,
            "invite_submit_bind",
            f"{student.email} 通过邀请提交并绑定",
        )
    elif project.student_id != student.id:
        raise HTTPException(403, "project already bound to another student")

    return await _create_submission(invite.project_id, file, user=student)


@router.post("/projects/{project_id}/submissions")
async def submit_paper(
    project_id: str,
    file: UploadFile = File(...),
    user: User | None = Depends(get_optional_user),
):
    if user:
        repo = get_repo()
        project = repo.get_project(project_id)
        if not project:
            raise HTTPException(404, "project not found")
        assert_project_student(project, user)
    else:
        raise HTTPException(401, "authentication required")

    return await _create_submission(project_id, file, user=user)


@router.get("/projects/{project_id}/rounds", response_model=list[SubmissionRound])
async def list_rounds(project_id: str, user: User = Depends(get_current_user)):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    return repo.list_rounds(project_id)


@router.get("/projects/{project_id}/rounds/{round_number}/report", response_model=MseRoundReport)
async def get_round_report(
    project_id: str,
    round_number: int,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")
    assert_round_visible(project, user, round_obj.review_status)

    issues = repo.list_issues(round_obj.id)
    report = None
    job = job_store.get(round_obj.job_id)
    if job and job.report:
        report = job.report

    diff = None
    if round_obj.diff_json:
        diff = RoundIssueDiff.model_validate(round_obj.diff_json)

    return repo.build_round_report(project, round_obj, report=report, diff=diff)


def _export_filename(project_title: str, round_number: int, ext: str) -> str:
    safe = "".join(
        c if c.isascii() and (c.isalnum() or c in "-_") else "_"
        for c in project_title
    ).strip("_")[:40]
    if not safe:
        safe = "mse_report"
    return f"{safe}_round{round_number}.{ext}"


@router.get("/projects/{project_id}/rounds/{round_number}/export.md")
async def export_round_markdown(
    project_id: str,
    round_number: int,
    user: User = Depends(get_current_user),
):
    from mse.export import export_round_markdown as build_md

    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")
    assert_round_visible(project, user, round_obj.review_status)

    issues = repo.list_issues(round_obj.id)
    content = build_md(
        project_title=project.title,
        round_number=round_number,
        issues=issues,
        gate_reason=round_obj.gate_reason,
        gate_passed=round_obj.gate_passed,
    )
    filename = _export_filename(project.title, round_number, "md")
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/rounds/{round_number}/export.pdf")
async def export_round_pdf(
    project_id: str,
    round_number: int,
    user: User = Depends(get_current_user),
):
    from mse.export import export_round_pdf_bytes

    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")
    assert_round_visible(project, user, round_obj.review_status)

    issues = repo.list_issues(round_obj.id)
    pdf = export_round_pdf_bytes(
        project_title=project.title,
        round_number=round_number,
        issues=issues,
        gate_reason=round_obj.gate_reason,
        gate_passed=round_obj.gate_passed,
    )
    filename = _export_filename(project.title, round_number, "pdf")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/projects/{project_id}/rounds/{round_number}/diff", response_model=RoundIssueDiff)
async def get_round_diff(
    project_id: str,
    round_number: int,
    base: int | None = None,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)

    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")

    if round_obj.diff_json:
        return RoundIssueDiff.model_validate(round_obj.diff_json)

    base_num = base if base is not None else round_number - 1
    if base_num < 1:
        return RoundIssueDiff(base_round=0, current_round=round_number)

    prev = repo.get_round(project_id, base_num)
    if not prev:
        raise HTTPException(404, "base round not found")

    curr_issues = repo.list_issues(round_obj.id)
    prev_issues = repo.list_issues(prev.id)
    dismissed = repo.list_dismissed_fingerprints(project_id)
    return diff_rounds(
        prev_issues,
        curr_issues,
        dismissed,
        base_round=base_num,
        current_round=round_number,
    )


@router.post("/projects/{project_id}/rounds/{round_number}/issues/{fingerprint}/dismiss")
async def dismiss_issue(
    project_id: str,
    round_number: int,
    fingerprint: str,
    body: DismissIssueRequest,
    user: User = Depends(get_current_user),
):
    require_role(user, UserRole.ADVISOR.value)
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_advisor(project, user)
    return repo.dismiss_issue(project_id, fingerprint, user.id, body.reason)


@router.post("/projects/{project_id}/rounds/{round_number}/release", response_model=MseRoundReport)
async def release_round(
    project_id: str,
    round_number: int,
    body: ReleaseRoundRequest,
    user: User = Depends(get_current_user),
):
    require_role(user, UserRole.ADVISOR.value)
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_advisor(project, user)

    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")
    if round_obj.review_status != ReviewStatus.PENDING_RELEASE:
        raise HTTPException(409, "round is not pending release")

    from mse.fsm import on_release

    issues = repo.list_issues(round_obj.id)
    gate_passed = bool(round_obj.gate_passed)
    project.status = on_release(project, gate_passed)
    round_obj.review_status = (
        ReviewStatus.PASSED if gate_passed else ReviewStatus.ISSUES_FOUND
    )
    round_obj.released_at = now_iso()
    repo.update_round(round_obj)
    repo.save_project(project)

    student = user_store.get(project.student_id) if project.student_id else None
    diff = RoundIssueDiff.model_validate(round_obj.diff_json) if round_obj.diff_json else None
    if student and not gate_passed:
        await notification_service.send_student_issues(
            student.email, project, round_number, issues, diff
        )
    elif gate_passed:
        job = job_store.get(round_obj.job_id)
        if job and job.document and not repo.get_innovation_review(project_id):
            from mse.innovation import build_innovation_review

            preview = build_innovation_review(project_id, round_obj.id, job.document)
            repo.save_innovation_review(preview)
        advisor = user_store.get(project.advisor_id) if project.advisor_id else None
        if advisor:
            await notification_service.send_advisor_ready(
                advisor.email, project, round_number
            )

    job = job_store.get(round_obj.job_id)
    report = job.report if job else None
    return repo.build_round_report(project, round_obj, report=report, diff=diff)


@router.post("/projects/{project_id}/rounds/{round_number}/retry")
async def retry_round(
    project_id: str,
    round_number: int,
    body: RetryRoundRequest,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)

    round_obj = repo.get_round(project_id, round_number)
    if not round_obj:
        raise HTTPException(404, "round not found")
    if round_obj.review_status not in (
        ReviewStatus.PARSE_FAILED,
        ReviewStatus.ANALYSIS_FAILED,
    ):
        raise HTTPException(409, "round is not in a retriable state")

    round_obj.review_status = ReviewStatus.PENDING
    repo.update_round(round_obj)
    await _enqueue_mse_round(project_id, round_obj.id)
    return {"status": "retrying", "round_id": round_obj.id}


@router.get("/projects/{project_id}/innovation-review", response_model=InnovationReview)
async def get_innovation_review(
    project_id: str,
    user: User = Depends(get_current_user),
):
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_member(project, user)
    review = repo.get_innovation_review(project_id)
    if not review:
        raise HTTPException(404, "innovation review not available")
    return review


@router.post("/projects/{project_id}/innovation-review", response_model=InnovationReview)
async def submit_innovation_review(
    project_id: str,
    body: SubmitInnovationReviewRequest,
    user: User = Depends(get_current_user),
):
    require_role(user, UserRole.ADVISOR.value)
    repo = get_repo()
    project = repo.get_project(project_id)
    if not project:
        raise HTTPException(404, "project not found")
    assert_project_advisor(project, user)
    if project.status not in (ProjectStatus.AWAITING_ADVISOR, ProjectStatus.COMPLETED):
        raise HTTPException(409, "project is not awaiting advisor review")

    try:
        review = repo.submit_innovation_decision(
            project_id,
            advisor_id=user.id,
            comment=body.advisor_comment,
            decision=body.advisor_decision,
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    student = user_store.get(project.student_id) if project.student_id else None
    if student:
        await notification_service.send_student_innovation_decision(
            student.email,
            project,
            review,
        )

    return review
