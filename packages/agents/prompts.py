from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPT_DIR = ROOT / "config" / "mse" / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def render_mse_review_user(
    *,
    section_title: str,
    section_text: str,
    rule_snippets: list[str],
    page_start: int,
    page_end: int,
) -> str:
    rules = "\n".join(f"- {s}" for s in rule_snippets) if rule_snippets else "（无额外规范片段）"
    return (
        f"章节：{section_title}\n"
        f"页码范围：第 {page_start}–{page_end} 页\n\n"
        f"适用规范片段：\n{rules}\n\n"
        f"待审文本：\n{section_text[:8000]}"
    )
