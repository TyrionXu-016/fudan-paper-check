from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from rule_bases.service import list_rule_base_ids, load_rule_base_yaml

_ROOT = Path(__file__).resolve().parents[2]
_INDEX_DIR = _ROOT / "data" / "rag"
_RULES_DIR = _ROOT / "config" / "rules"
_GBT7714_PATH = _ROOT / "config" / "rules" / "gbt7714.md"


@dataclass
class RuleChunk:
    id: str
    rule_base_id: str
    dimension: str
    text: str
    source: str


def index_path(rule_base_id: str) -> Path:
    return _INDEX_DIR / f"{rule_base_id}.json"


def _chunk_from_text(
    *,
    rule_base_id: str,
    dimension: str,
    text: str,
    source: str,
    chunk_index: int,
) -> RuleChunk:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", source).strip("-") or "chunk"
    return RuleChunk(
        id=f"{rule_base_id}:{slug}:{chunk_index}",
        rule_base_id=rule_base_id,
        dimension=dimension,
        text=text.strip(),
        source=source,
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


def _chunks_from_yaml(rule_base_id: str) -> list[RuleChunk]:
    data = load_rule_base_yaml(rule_base_id)
    chunks: list[RuleChunk] = []
    idx = 0

    summary = data.get("summary") or {}
    for dimension, text in summary.items():
        if text:
            chunks.append(
                _chunk_from_text(
                    rule_base_id=rule_base_id,
                    dimension=str(dimension),
                    text=str(text),
                    source=f"{rule_base_id}.yaml#summary.{dimension}",
                    chunk_index=idx,
                )
            )
            idx += 1

    for field in ("required_sections", "optional_sections"):
        values = data.get(field) or []
        if values:
            chunks.append(
                _chunk_from_text(
                    rule_base_id=rule_base_id,
                    dimension="format",
                    text=f"{field}: {', '.join(values)}",
                    source=f"{rule_base_id}.yaml#{field}",
                    chunk_index=idx,
                )
            )
            idx += 1

    patterns = data.get("patterns") or {}
    for name, pattern in patterns.items():
        chunks.append(
            _chunk_from_text(
                rule_base_id=rule_base_id,
                dimension="format",
                text=f"pattern {name}: {pattern}",
                source=f"{rule_base_id}.yaml#patterns.{name}",
                chunk_index=idx,
            )
        )
        idx += 1

    warnings = data.get("warnings") or {}
    for name, pattern in warnings.items():
        chunks.append(
            _chunk_from_text(
                rule_base_id=rule_base_id,
                dimension="format",
                text=f"warning {name}: {pattern}",
                source=f"{rule_base_id}.yaml#warnings.{name}",
                chunk_index=idx,
            )
        )
        idx += 1

    return chunks


def _chunks_from_gbt7714(rule_base_id: str, start_index: int) -> list[RuleChunk]:
    chunks: list[RuleChunk] = []
    idx = start_index
    for title, body in _split_markdown_sections(_GBT7714_PATH):
        chunks.append(
            _chunk_from_text(
                rule_base_id=rule_base_id,
                dimension="reference",
                text=f"{title}\n{body}",
                source=f"gbt7714.md#{title}",
                chunk_index=idx,
            )
        )
        idx += 1
    return chunks


def _chunks_from_rule_markdown(rule_base_id: str, start_index: int) -> list[RuleChunk]:
    path = _RULES_DIR / f"{rule_base_id}.md"
    chunks: list[RuleChunk] = []
    idx = start_index
    for title, body in _split_markdown_sections(path):
        chunks.append(
            _chunk_from_text(
                rule_base_id=rule_base_id,
                dimension="format",
                text=f"{title}\n{body}",
                source=f"{path.name}#{title}",
                chunk_index=idx,
            )
        )
        idx += 1
    return chunks


def build_index(rule_base_id: str) -> Path:
    chunks = _chunks_from_yaml(rule_base_id)
    chunks.extend(_chunks_from_rule_markdown(rule_base_id, len(chunks)))
    chunks.extend(_chunks_from_gbt7714(rule_base_id, len(chunks)))

    payload = {
        "rule_base_id": rule_base_id,
        "chunk_count": len(chunks),
        "chunks": [asdict(chunk) for chunk in chunks],
    }
    dest = index_path(rule_base_id)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def list_indexed_rule_bases() -> list[str]:
    if not _INDEX_DIR.exists():
        return []
    return sorted(p.stem for p in _INDEX_DIR.glob("*.json"))


def load_index(rule_base_id: str) -> dict | None:
    path = index_path(rule_base_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_all_indexes() -> list[Path]:
    built: list[Path] = []
    for rule_id in list_rule_base_ids():
        built.append(build_index(rule_id))
    return built


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build RAG rule indexes from journal YAML")
    parser.add_argument("--rule-base", dest="rule_base", help="single rule base id")
    parser.add_argument("--all", action="store_true", help="index all rule bases")
    args = parser.parse_args(argv)

    if args.all:
        paths = build_all_indexes()
        for path in paths:
            print(path)
        return 0

    if not args.rule_base:
        parser.error("specify --rule-base ID or --all")

    path = build_index(args.rule_base)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
