from __future__ import annotations

import json
from pathlib import Path

from schema.models import Decision
from storage.jobs import STORAGE, now_iso


DECISIONS_DIR = STORAGE.parent / "decisions"


def _path(task_id: str) -> Path:
    DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
    return DECISIONS_DIR / f"{task_id}.json"


def load_decisions(task_id: str) -> dict[str, Decision]:
    path = _path(task_id)
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    items = [Decision.model_validate(item) for item in json.loads(raw)]
    return {d.issue_id: d for d in items}


def save_decisions(task_id: str, decisions: dict[str, Decision]) -> None:
    path = _path(task_id)
    payload = [d.model_dump(mode="json") for d in decisions.values()]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_decisions(task_id: str, incoming: list[Decision]) -> dict[str, Decision]:
    current = load_decisions(task_id)
    ts = now_iso()
    for item in incoming:
        data = item.model_dump()
        data["updated_at"] = ts
        current[item.issue_id] = Decision.model_validate(data)
    save_decisions(task_id, current)
    return current


def patch_decision(task_id: str, issue_id: str, decision: Decision) -> Decision:
    current = load_decisions(task_id)
    data = decision.model_dump()
    data["issue_id"] = issue_id
    data["updated_at"] = now_iso()
    saved = Decision.model_validate(data)
    current[issue_id] = saved
    save_decisions(task_id, current)
    return saved


def clear_decisions(task_id: str) -> None:
    path = _path(task_id)
    if path.exists():
        path.unlink()
