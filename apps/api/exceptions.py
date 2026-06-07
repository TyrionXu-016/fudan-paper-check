from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from schema.api_response import ApiError, ApiResponse


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        body = ApiResponse.error(exc.code, exc.message, exc.detail).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = str(exc.status_code)
        if isinstance(exc.detail, dict):
            message = exc.detail.get("message", str(exc.detail))
            detail = exc.detail.get("detail")
        else:
            message = str(exc.detail)
            detail = None
        body = ApiResponse.error(code, message, detail).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        body = ApiResponse.error(
            "VALIDATION_ERROR",
            "request validation failed",
            detail=str(exc.errors()),
        ).model_dump()
        return JSONResponse(status_code=422, content=body)
