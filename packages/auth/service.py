from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schema.models import JobRecord, UserPublic
from storage.jobs import job_store
from storage.users import JWT_ALGORITHM, JWT_EXPIRE_HOURS, JWT_SECRET, User, now_iso, user_store


security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    )
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest = password_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    )
    return secrets.compare_digest(check.hex(), digest)


def create_access_token(user_id: str, role: str = "advisor") -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
        return user_id
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token") from exc


def to_public(user: User) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, name=user.name, role=getattr(user, "role", "advisor"))


def get_or_create_student(email: str) -> User:
    """Provision a student account for invite-based first submission."""
    existing = user_store.get_by_email(email)
    if existing:
        if getattr(existing, "role", "advisor") != "student":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "email registered with non-student role")
        return existing
    user = User(
        id=str(uuid.uuid4()),
        email=email.lower(),
        name=email.split("@")[0],
        password_hash=hash_password(secrets.token_urlsafe(32)),
        role="student",
        created_at=now_iso(),
    )
    user_store.save(user)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    user_id = decode_token(credentials.credentials)
    user = user_store.get(user_id)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "user not found")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def assert_job_owner(job: JobRecord, user: User) -> None:
    if job.user_id and job.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
