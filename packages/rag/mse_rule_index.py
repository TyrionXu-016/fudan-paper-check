from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_MSE_INDEX_ROOT = _ROOT / "data" / "rag" / "mse"
_DEFAULT_SPECS = [
    _ROOT / "config" / "mse" / "default_spec.md",
    _ROOT / "config" / "mse" / "thesis_common_problems.md",
]


@dataclass
class MseRuleChunk:
    id: str
    project_id: str
    dimension: str
    text: str
    source: str


def project_index_path(project_id: str) -> Path:
    return _MSE_INDEX_ROOT / project_id / "index.json"


def project_sources_dir(project_id: str) -> Path:
    return _MSE_INDEX_ROOT / project_id / "sources"


def rebuild_project_index_from_sources(
    project_id: str,
    *,
    include_default: bool = True,
) -> Path:
    sources = project_sources_dir(project_id)
    spec_paths = sorted(sources.glob("*.md")) if sources.exists() else []
    return build_project_index(
        project_id,
        spec_paths=spec_paths,
        include_default=include_default,
    )


def _split_markdown_sections(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    sections: list[tuple[str, str]] = []
    current_title = "overview"
    current_lines: list[str] = []
    for line in raw.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.lstrip("#").strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))
    return [(title, body) for title, body in sections if body]


def _chunk_text(
    *,
    project_id: str,
    dimension: str,
    text: str,
    source: str,
    chunk_index: int,
) -> MseRuleChunk:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", source).strip("-") or "chunk"
    return MseRuleChunk(
        id=f"mse:{project_id}:{slug}:{chunk_index}",
        project_id=project_id,
        dimension=dimension,
        text=text.strip(),
        source=source,
    )


def build_project_index(
    project_id: str,
    *,
    spec_paths: list[Path] | None = None,
    include_default: bool = True,
) -> Path:
    paths = list(spec_paths or [])
    if include_default:
        defaults = [p for p in _DEFAULT_SPECS if p.exists()]
        paths = defaults + paths

    chunks: list[MseRuleChunk] = []
    idx = 0
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        for title, body in _split_markdown_sections(resolved):
            chunks.append(
                _chunk_text(
                    project_id=project_id,
                    dimension="mse_spec",
                    text=f"{title}\n{body}",
                    source=f"{resolved.name}#{title}",
                    chunk_index=idx,
                )
            )
            idx += 1

    payload = {
        "project_id": project_id,
        "chunk_count": len(chunks),
        "chunks": [asdict(c) for c in chunks],
    }
    dest = project_index_path(project_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def load_project_index(project_id: str) -> dict | None:
    path = project_index_path(project_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
