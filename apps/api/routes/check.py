from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from api.services.upload import CHECK_ALLOWED_SUFFIXES, create_check_job
from auth.service import get_current_user
from schema.api_response import ApiResponse
from schema.models import CheckSubmitResponse, JobStatus
from storage.users import User

router = APIRouter(prefix="/v1", tags=["check"])


@router.post("/check", status_code=202)
async def submit_check(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mineru_file: UploadFile | None = File(None),
    rule_base_id: str = Form("generic"),
    user: User = Depends(get_current_user),
) -> ApiResponse[CheckSubmitResponse]:
    record = await create_check_job(
        background_tasks,
        user_id=user.id,
        file=file,
        mineru_file=mineru_file,
        rule_base_id=rule_base_id,
        allowed_suffixes=CHECK_ALLOWED_SUFFIXES,
    )
    return ApiResponse.success(
        CheckSubmitResponse(task_id=record.job_id, status=JobStatus.QUEUED)
    )
