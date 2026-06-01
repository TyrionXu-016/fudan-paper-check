from __future__ import annotations

import asyncio
import json
import os
import uuid
from pathlib import Path

from mse.fsm import on_analysis_complete, on_release
from mse.gate import evaluate_gate
from mse.issue_diff import diff_rounds
from mse.models import ProjectStatus, ReviewStatus
from notify.service import notification_service
from schema.models import DetectStage, IssueSeverity, JobRecord, JobStatus
from storage.db import get_session, init_db
from storage.jobs import STORAGE, UPLOADS, job_store, now_iso
from storage.mse_repository import MseRepository
from storage.users import user_store


async def process_mse_round(ctx: dict, project_id: str, round_id: str) -> dict:
    init_db()
    session = get_session()
    repo = MseRepository(session)
    try:
        round_obj = repo.get_round_by_id(round_id)
        if not round_obj:
            return {"error": "round not found"}
        project = repo.get_project(project_id)
        if not project:
            return {"error": "project not found"}

        round_obj.review_status = ReviewStatus.PARSING
        repo.update_round(round_obj)

        record = job_store.get(round_obj.job_id)
        if not record:
            return {"error": "job not found"}

        try:
            convert_suffixes = {
                ".pdf",
                ".jpg",
                ".jpeg",
                ".png",
                ".tiff",
                ".webp",
                ".zip",
            }
            upload_path = None
            out_dir = UPLOADS / round_obj.job_id
            if record.filename:
                candidate = out_dir / record.filename
                if candidate.exists() and candidate.suffix.lower() in convert_suffixes:
                    upload_path = candidate
            if upload_path is None and out_dir.exists():
                for f in sorted(out_dir.iterdir()):
                    if f.is_file() and f.suffix.lower() in convert_suffixes:
                        upload_path = f
                        break

            if upload_path and upload_path.exists():
                from worker.mse_converter import MseDocumentConverter

                converter = MseDocumentConverter()
                max_retries = int(os.getenv("MINERU_MAX_RETRIES", "2"))
                last_err: Exception | None = None
                maker_path = mineru_path = None
                for attempt in range(max_retries + 1):
                    try:
                        maker_path, mineru_path = await asyncio.to_thread(
                            converter.convert, upload_path, out_dir
                        )
                        break
                    except Exception as exc:
                        last_err = exc
                        if attempt < max_retries:
                            await asyncio.sleep(2**attempt)
                if maker_path is None:
                    raise last_err or RuntimeError("conversion failed")

                from worker.tasks import process_paper_job

                await process_paper_job(
                    ctx,
                    round_obj.job_id,
                    str(maker_path),
                    str(mineru_path) if mineru_path else None,
                    record.journal_profile or "generic",
                )
            else:
                from worker.tasks import process_paper_job

                maker = UPLOADS / round_obj.job_id / "paper_maker.md"
                mineru = UPLOADS / round_obj.job_id / "paper_mineru.md"
                if not maker.exists():
                    raise FileNotFoundError("no upload found for mse round")
                await process_paper_job(
                    ctx,
                    round_obj.job_id,
                    str(maker),
                    str(mineru) if mineru.exists() else None,
                    record.journal_profile or "generic",
                )
        except Exception as exc:
            round_obj.review_status = ReviewStatus.PARSE_FAILED
            round_obj.analyzed_at = now_iso()
            repo.update_round(round_obj)
            project.status = ProjectStatus.ACTIVE
            repo.save_project(project)
            student = user_store.get(project.student_id) if project.student_id else None
            if student:
                await notification_service.send_parse_failed(
                    student.email, project, round_obj.round_number
                )
            repo.log_activity(project_id, None, "parse_failed", str(exc))
            session.commit()
            return {"status": "parse_failed", "error": str(exc)}

        record = job_store.get(round_obj.job_id)
        if not record or record.status == JobStatus.FAILED:
            round_obj.review_status = ReviewStatus.ANALYSIS_FAILED
            round_obj.analyzed_at = now_iso()
            repo.update_round(round_obj)
            err = record.error if record else "unknown"
            student = user_store.get(project.student_id) if project.student_id else None
            if student:
                await notification_service.send_analysis_failed(
                    student.email, project, round_obj.round_number, err or ""
                )
            session.commit()
            return {"status": "analysis_failed"}

        round_obj.review_status = ReviewStatus.ANALYZING
        repo.update_round(round_obj)

        maker = UPLOADS / round_obj.job_id / "paper_maker.md"
        mineru = UPLOADS / round_obj.job_id / "paper_mineru.md"
        base_issues = record.report.issues if record.report else []
        if record.document:
            from mse.analyzer import run_mse_analysis

            issues, spans = run_mse_analysis(
                record.document,
                base_issues,
                project_id=project_id,
                journal_profile=record.journal_profile or "generic",
                maker_path=str(maker) if maker.exists() else None,
                mineru_path=str(mineru) if mineru.exists() else None,
                spans=record.spans,
            )
            record.spans = spans
            if record.report:
                record.report.issues = issues
            job_store.save(record)
        else:
            issues = base_issues

        repo.save_issues(round_obj.id, round_obj.job_id, issues)

        prev_round = (
            repo.get_round(project_id, round_obj.round_number - 1)
            if round_obj.round_number > 1
            else None
        )
        prev_issues = repo.list_issues(prev_round.id) if prev_round else []
        dismissed = repo.list_dismissed_fingerprints(project_id)
        diff = diff_rounds(
            prev_issues,
            issues,
            dismissed,
            base_round=prev_round.round_number if prev_round else 0,
            current_round=round_obj.round_number,
        )
        round_obj.diff_json = diff.model_dump(mode="json")

        gate = evaluate_gate(round_obj.id, issues)
        round_obj.gate_passed = gate.passed
        round_obj.gate_reason = gate.reason
        round_obj.notify_target = gate.notify_target
        round_obj.issue_count = len(issues)
        round_obj.error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        round_obj.warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        round_obj.analyzed_at = now_iso()

        pending_release = not project.auto_notify_student
        project_status, review_status = on_analysis_complete(
            project,
            gate_passed=gate.passed,
            pending_release=pending_release and not gate.passed,
        )
        if pending_release and not gate.passed:
            round_obj.review_status = ReviewStatus.PENDING_RELEASE
            project.status = ProjectStatus.ANALYZING
        elif gate.passed:
            round_obj.review_status = ReviewStatus.PASSED
            round_obj.released_at = now_iso()
            project.status = ProjectStatus.AWAITING_ADVISOR
        else:
            round_obj.review_status = ReviewStatus.ISSUES_FOUND
            round_obj.released_at = now_iso()
            project.status = ProjectStatus.ACTIVE

        repo.update_round(round_obj)
        repo.save_project(project)
        repo.log_activity(
            project_id,
            None,
            "analysis_complete",
            f"第 {round_obj.round_number} 轮分析完成",
        )

        if gate.passed and record.document:
            if not repo.get_innovation_review(project_id):
                from mse.innovation import build_innovation_review

                preview = build_innovation_review(
                    project_id, round_obj.id, record.document
                )
                repo.save_innovation_review(preview)

        advisor = user_store.get(project.advisor_id) if project.advisor_id else None
        student = user_store.get(project.student_id) if project.student_id else None

        if round_obj.review_status == ReviewStatus.PENDING_RELEASE and advisor:
            await notification_service.send_advisor_preview_ready(
                advisor.email, project, round_obj.round_number
            )
        elif not pending_release or gate.passed:
            if gate.passed and advisor:
                await notification_service.send_advisor_ready(
                    advisor.email, project, round_obj.round_number
                )
            elif student and not gate.passed:
                await notification_service.send_student_issues(
                    student.email,
                    project,
                    round_obj.round_number,
                    issues,
                    diff,
                )

        session.commit()
        return {"status": round_obj.review_status.value, "gate_passed": gate.passed}
    finally:
        session.close()


async def retry_mse_round_parse(ctx: dict, project_id: str, round_id: str) -> dict:
    return await process_mse_round(ctx, project_id, round_id)
