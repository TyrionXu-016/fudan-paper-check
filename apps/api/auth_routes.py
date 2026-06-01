from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from auth.service import create_access_token, get_current_user, hash_password, to_public, verify_password
from schema.models import JobListItem, LoginRequest, RegisterRequest, TokenResponse, UserPublic
from storage.jobs import job_store
from storage.users import User, now_iso, user_store

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    if user_store.get_by_email(body.email):
        raise HTTPException(409, "email already registered")
    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        name=body.name or body.email.split("@")[0],
        password_hash=hash_password(body.password),
        role=body.role if body.role in ("advisor", "student") else "advisor",
        created_at=now_iso(),
    )
    user_store.save(user)
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=to_public(user))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    user = user_store.get_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid email or password")
    token = create_access_token(user.id, getattr(user, "role", "advisor"))
    return TokenResponse(access_token=token, user=to_public(user))


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)):
    return to_public(user)


def job_to_list_item(record) -> JobListItem:
    report = record.report
    return JobListItem(
        job_id=record.job_id,
        status=record.status,
        journal_profile=record.journal_profile,
        filename=record.filename,
        paper_title=report.paper_title if report else None,
        summary=report.summary if report else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/jobs", response_model=list[JobListItem])
async def list_my_jobs(user: User = Depends(get_current_user)):
    records = job_store.list_by_user(user.id)
    return [job_to_list_item(r) for r in records]
