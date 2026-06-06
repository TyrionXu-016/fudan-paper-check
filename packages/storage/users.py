from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import func


ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = ROOT / "data" / "users.json"


class User(BaseModel):
    id: str
    email: str
    name: str = ""
    password_hash: str
    role: str = "advisor"
    created_at: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class UserStore:
    users: dict[str, User] = field(default_factory=dict)

    @staticmethod
    def _from_orm(row) -> User:
        return User(
            id=row.id,
            email=row.email,
            name=row.name or "",
            password_hash=row.password_hash,
            role=row.role or "advisor",
            created_at=row.created_at or "",
        )

    def _session(self):
        from storage.db import get_session, init_db

        init_db()
        return get_session()

    def load(self) -> None:
        """Compatibility shim: migrate legacy JSON users into SQLite."""
        self.migrate_json_once()

    def save(self, user: User) -> None:
        from storage.models_orm import UserORM

        session = self._session()
        try:
            row = session.get(UserORM, user.id)
            if row is None:
                row = UserORM(id=user.id)
                session.add(row)
            row.email = user.email.lower()
            row.name = user.name or ""
            row.password_hash = user.password_hash
            row.role = user.role or "advisor"
            row.created_at = user.created_at or now_iso()
            session.commit()
            self.users[user.id] = self._from_orm(row)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get(self, user_id: str) -> Optional[User]:
        from storage.models_orm import UserORM

        session = self._session()
        try:
            row = session.get(UserORM, user_id)
            return self._from_orm(row) if row else None
        finally:
            session.close()

    def get_by_email(self, email: str) -> Optional[User]:
        from storage.models_orm import UserORM

        email_lower = email.lower()
        session = self._session()
        try:
            row = (
                session.query(UserORM)
                .filter(func.lower(UserORM.email) == email_lower)
                .one_or_none()
            )
            return self._from_orm(row) if row else None
        finally:
            session.close()

    def migrate_json_once(self) -> int:
        """Import legacy data/users.json into SQLite without rewriting JSON."""
        from storage.models_orm import UserORM

        if not USERS_FILE.exists():
            return 0

        raw = json.loads(USERS_FILE.read_text(encoding="utf-8") or "{}")
        if not isinstance(raw, dict) or not raw:
            return 0

        session = self._session()
        imported = 0
        try:
            for uid, item in raw.items():
                if not isinstance(item, dict):
                    continue
                data = dict(item)
                data.setdefault("id", uid)
                data.setdefault("role", "advisor")
                data.setdefault("created_at", "")
                user = User.model_validate(data)
                existing = session.get(UserORM, user.id)
                if existing is None:
                    existing = (
                        session.query(UserORM)
                        .filter(func.lower(UserORM.email) == user.email.lower())
                        .one_or_none()
                    )
                if existing is not None:
                    continue
                session.add(
                    UserORM(
                        id=user.id,
                        email=user.email.lower(),
                        name=user.name or "",
                        password_hash=user.password_hash,
                        role=user.role or "advisor",
                        created_at=user.created_at or now_iso(),
                    )
                )
                imported += 1
            if imported:
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
                shutil.copy2(USERS_FILE, USERS_FILE.with_name(f"{USERS_FILE.name}.bak-{stamp}"))
            session.commit()
            return imported
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


user_store = UserStore()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))
