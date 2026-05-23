from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = ROOT / "data" / "users.json"


class User(BaseModel):
    id: str
    email: str
    name: str = ""
    password_hash: str
    created_at: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class UserStore:
    users: dict[str, User] = field(default_factory=dict)

    def _persist(self) -> None:
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {uid: user.model_dump() for uid, user in self.users.items()}
        USERS_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load(self) -> None:
        if not USERS_FILE.exists():
            return
        raw = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        self.users = {uid: User.model_validate(item) for uid, item in raw.items()}

    def save(self, user: User) -> None:
        self.users[user.id] = user
        self._persist()

    def get(self, user_id: str) -> Optional[User]:
        if not self.users:
            self.load()
        return self.users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        if not self.users:
            self.load()
        email_lower = email.lower()
        for user in self.users.values():
            if user.email.lower() == email_lower:
                return user
        return None


user_store = UserStore()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))
