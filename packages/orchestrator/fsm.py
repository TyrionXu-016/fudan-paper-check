from __future__ import annotations

from schema.api_response import ERROR_TASK_BUSY, ApiError
from schema.models import JobRecord, JobStatus

ACTIVE_STATUSES = frozenset(
    {
        JobStatus.QUEUED,
        JobStatus.CONVERTING,
        JobStatus.PARSING,
        JobStatus.CHECKING,
    }
)


def is_job_active(record: JobRecord) -> bool:
    return record.status in ACTIVE_STATUSES


def assert_can_restart(record: JobRecord) -> None:
    if is_job_active(record):
        raise ApiError(
            ERROR_TASK_BUSY,
            f"task is still running, status={record.status.value}",
            status_code=409,
        )
