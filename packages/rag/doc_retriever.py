from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rag.doc_index import _task_index_path


@dataclass
class ContextSnippet:
    span_id: str
    text: str
    role: str
    score: float


def retrieve_context(
    task_id: str,
    span_id: str,
    *,
    window: int = 2,
    top_k: int = 8,
    include_section_summary: bool = True,
) -> list[ContextSnippet]:
    """
    Retrieve adjacent context for a given span from the task index.
    """
    dest = _task_index_path(task_id)
    if not dest.exists():
        return []

    data = json.loads(dest.read_text(encoding="utf-8"))
    spans_data = {s["id"]: s for s in data.get("spans", [])}
    
    if span_id not in spans_data:
        return []
        
    target_span = spans_data[span_id]
    results = []
    
    # 1. Target span itself
    results.append(
        ContextSnippet(
            span_id=target_span["id"],
            text=target_span["text"],
            role="target",
            score=1.0,
        )
    )
    
    # 2. Neighbors
    for n_id in target_span.get("neighbors", []):
        if n_id in spans_data:
            n_span = spans_data[n_id]
            results.append(
                ContextSnippet(
                    span_id=n_span["id"],
                    text=n_span["text"],
                    role="neighbor",
                    score=0.8, # Simple static score for MVP
                )
            )

    # 3. Section boundaries (first and last span of the section)
    if include_section_summary:
        sec_id = target_span.get("section_id")
        section = next((s for s in data.get("sections", []) if s["id"] == sec_id), None)
        if section and section.get("span_ids"):
            first_id = section["span_ids"][0]
            last_id = section["span_ids"][-1]
            if first_id not in target_span.get("neighbors", []) and first_id != target_span["id"]:
                if first_id in spans_data:
                    results.append(
                        ContextSnippet(
                            span_id=first_id,
                            text=spans_data[first_id]["text"],
                            role="section_start",
                            score=0.5,
                        )
                    )
    
    # We sort by score descending and return up to top_k
    results.sort(key=lambda c: c.score, reverse=True)
    return results[:top_k]
