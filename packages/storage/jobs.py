from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from schema.models import JobRecord


ROOT = Path(__file__).resolve().parents[2]
STORAGE = ROOT / "data" / "jobs"
UPLOADS = ROOT / "data" / "uploads"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobStore:
    jobs: dict[str, JobRecord] = field(default_factory=dict)

    def save(self, record: JobRecord) -> None:
        self.jobs[record.job_id] = record
        STORAGE.mkdir(parents=True, exist_ok=True)
        (STORAGE / f"{record.job_id}.json").write_text(
            record.model_dump_json(indent=2), encoding="utf-8"
        )

    def get(self, job_id: str) -> JobRecord | None:
        path = STORAGE / f"{job_id}.json"
        if path.exists():
            record = JobRecord.model_validate_json(path.read_text(encoding="utf-8"))
            self.jobs[job_id] = record
            return record
        return self.jobs.get(job_id)

    def list_all(self) -> list[JobRecord]:
        STORAGE.mkdir(parents=True, exist_ok=True)
        for path in STORAGE.glob("*.json"):
            if path.name.endswith(".report.md"):
                continue
            job_id = path.stem
            self.get(job_id)
        records = list(self.jobs.values())
        records.sort(key=lambda r: r.created_at or "", reverse=True)
        return records

    def list_by_user(self, user_id: str, limit: int = 50) -> list[JobRecord]:
        return [r for r in self.list_all() if r.user_id == user_id][:limit]


job_store = JobStore()
