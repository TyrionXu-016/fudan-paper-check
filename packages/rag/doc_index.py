from __future__ import annotations

import json
from pathlib import Path

from schema.models import PaperDocument, Span

_ROOT = Path(__file__).resolve().parents[2]
_TASKS_DIR = _ROOT / "data" / "rag" / "tasks"


def _task_index_path(task_id: str) -> Path:
    return _TASKS_DIR / f"{task_id}.json"


def build_task_index(task_id: str, doc: PaperDocument, spans: list[Span]) -> Path:
    """
    Builds a temporary JSON index for RAG-2 context retrieval.
    Includes neighbors computation.
    """
    _TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    indexed_spans = []
    for i, span in enumerate(spans):
        # Determine neighbors within window 2
        neighbors = []
        for j in range(max(0, i - 2), min(len(spans), i + 3)):
            if i != j:
                neighbors.append(spans[j].id)
                
        indexed_spans.append({
            "id": span.id,
            "section_id": span.section_id,
            "text": span.text,
            "line_start": span.line_start,
            "line_end": span.line_end,
            "neighbors": neighbors,
            "tags": [] # Placeholder for future tagging
        })

    sections = [
        {
            "id": s.id, 
            "kind": s.kind.value, 
            "title": s.title,
            "span_ids": [sp.id for sp in spans if sp.section_id == s.id]
        }
        for s in doc.sections
    ]
    
    payload = {
        "task_id": task_id,
        "paper_title": doc.meta.title,
        "spans": indexed_spans,
        "sections": sections,
    }
    
    dest = _task_index_path(task_id)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def drop_task_index(task_id: str) -> None:
    """Removes the temporary index for a given task ID."""
    dest = _task_index_path(task_id)
    if dest.exists():
        dest.unlink()
