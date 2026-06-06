from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int | str = 0
    message: str = "ok"
    data: T | None = None

    @classmethod
    def success(cls, data: T, message: str = "ok") -> ApiResponse[T]:
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        detail: str | None = None,
    ) -> ApiResponse[None]:
        payload: dict[str, Any] = {"code": code, "message": message, "data": None}
        if detail is not None:
            payload["detail"] = detail
        return cls.model_validate(payload)


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        detail: str | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


# Standard error codes (Feishu contract)
ERROR_DETECT_FAILED = "DETECT_FAILED"
ERROR_FILE_TOO_LARGE = "FILE_TOO_LARGE"
ERROR_UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
ERROR_TASK_NOT_FOUND = "TASK_NOT_FOUND"
ERROR_TASK_NOT_READY = "TASK_NOT_READY"
ERROR_RULE_BASE_NOT_FOUND = "RULE_BASE_NOT_FOUND"
ERROR_RAG_INDEX_NOT_READY = "RAG_INDEX_NOT_READY"
ERROR_TASK_BUSY = "TASK_BUSY"
