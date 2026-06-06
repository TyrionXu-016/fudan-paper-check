from orchestrator.fsm import assert_can_restart, is_job_active
from orchestrator.preview import build_preview, count_unresolved
from schema.api_response import ApiError
from schema.models import (
    CheckCategory,
    CheckReport,
    Decision,
    DecisionAction,
    Issue,
    IssueSeverity,
    JobRecord,
    JobStatus,
    ParseQuality,
    ReportSummary,
    Span,
)


def test_fsm_active_detection():
    record = JobRecord(job_id="j1", status=JobStatus.CHECKING)
    assert is_job_active(record) is True

    done = JobRecord(job_id="j2", status=JobStatus.DONE)
    assert is_job_active(done) is False


def test_fsm_restart_blocked():
    record = JobRecord(job_id="j1", status=JobStatus.PARSING)
    try:
        assert_can_restart(record)
        assert False, "expected ApiError"
    except ApiError as exc:
        assert exc.code == "TASK_BUSY"


def test_preview_applies_accept_decision():
    span = Span(
        id="s1",
        section_id="sec1",
        block_id="b1",
        start_offset=0,
        end_offset=5,
        text="原文",
    )
    issue = Issue(
        id="i1",
        code="TEST",
        category=CheckCategory.FORMAT,
        severity=IssueSeverity.WARNING,
        message="fix",
        suggestion="改后",
        suggested_text="改后",
        span_id="s1",
    )
    record = JobRecord(
        job_id="t1",
        status=JobStatus.DONE,
        spans=[span],
        report=CheckReport(
            job_id="t1",
            parse_quality=ParseQuality(),
            summary=ReportSummary(),
            issues=[issue],
            paper_title="测试",
        ),
    )
    decisions = {
        "i1": Decision(issue_id="i1", action=DecisionAction.ACCEPT),
    }
    preview = build_preview(record, decisions)
    assert preview.spans[0].text == "改后"
    assert preview.spans[0].highlight == "accepted"
    assert count_unresolved(record.report.issues, decisions) == 0
