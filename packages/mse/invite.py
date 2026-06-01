from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from mse.models import InitiatorRole, UserRole

INVITE_SECRET = os.getenv("MSE_INVITE_SECRET", os.getenv("JWT_SECRET", "dev-invite-secret"))
INVITE_TTL_DAYS = int(os.getenv("MSE_INVITE_TTL_DAYS", "7"))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def generate_invite_token(
    project_id: str,
    target_role: UserRole,
    target_email: str,
) -> tuple[str, str]:
    """Return (token, expires_at iso)."""
    nonce = secrets.token_urlsafe(16)
    expires = _now() + timedelta(days=INVITE_TTL_DAYS)
    payload = f"{project_id}|{target_role.value}|{target_email.lower()}|{expires.timestamp()}|{nonce}"
    sig = hmac.new(INVITE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    token = f"{nonce}.{sig[:32]}"
    return token, expires.isoformat()


def verify_invite_token(
    token: str,
    project_id: str,
    target_role: UserRole,
    target_email: str,
    expires_at: str,
) -> bool:
    try:
        expires = datetime.fromisoformat(expires_at)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if _now() > expires:
            return False
        nonce, sig = token.split(".", 1)
        payload = f"{project_id}|{target_role.value}|{target_email.lower()}|{expires.timestamp()}|{nonce}"
        expected = hmac.new(INVITE_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(sig, expected)
    except (ValueError, TypeError):
        return False


def invite_target_for_project(
    initiator_role: InitiatorRole,
    *,
    has_advisor: bool,
    has_student: bool,
) -> UserRole | None:
    if not has_student and initiator_role == InitiatorRole.ADVISOR:
        return UserRole.STUDENT
    if not has_advisor and initiator_role == InitiatorRole.STUDENT:
        return UserRole.ADVISOR
    return None
