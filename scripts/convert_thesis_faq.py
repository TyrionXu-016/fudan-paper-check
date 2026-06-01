#!/usr/bin/env python3
"""Convert thesis FAQ PDF to structured markdown for MSE RAG indexing."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "config/mse/sources/thesis_common_problems.pdf"
DEFAULT_MD = ROOT / "config/mse/thesis_common_problems.md"

_PART_RE = re.compile(r"^PART\s*$", re.I)
_PART_NUM_RE = re.compile(r"^0?([1-3])\s*$")
_SECTION_TITLES = {
    "论文的格式、结构和文字表达": "论文的格式、结构和文字表达",
    "论文的写法与内容": "论文的写法与内容",
    "论文的写法和内容": "论文的写法与内容",
    "学术不端行为": "学术不端行为",
}
_BULLET_MAIN = "\uf06c"
_BULLET_SUB = "\uf075"


def _extract_pages(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit("Install pypdf: python3 -m pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def _normalize_line(line: str) -> str:
    return line.strip().replace("\u3000", " ").strip()


def _is_topic_heading(text: str) -> bool:
    if len(text) > 48 or text.startswith("“"):
        return False
    if "专家评语" in text:
        return False
    markers = ("要求", "要求：", "要求:", "说明")
    return any(text.endswith(m) for m in markers) or len(text) < 22


def _structure_lines(pages: list[str]) -> list[str]:
    out: list[str] = [
        "# 论文常见问题",
        "",
        "<!-- 来源: config/mse/sources/thesis_common_problems.pdf | 更新: 2026-05 -->",
        "",
    ]
    seen_h2: set[str] = set()

    for page_text in pages:
        if not page_text:
            continue
        lines = [_normalize_line(l) for l in page_text.splitlines()]
        i = 0
        while i < len(lines):
            line = lines[i]
            if not line or line in {"CONTENTS", "目 录", "01", "02", "03"}:
                i += 1
                continue
            if re.fullmatch(r"0[1-3]", line):
                i += 1
                continue
            if _PART_RE.match(line):
                i += 2 if i + 1 < len(lines) and _PART_NUM_RE.match(lines[i + 1]) else 1
                continue
            if line in _SECTION_TITLES:
                title = _SECTION_TITLES[line]
                if title not in seen_h2:
                    seen_h2.add(title)
                    out.extend(["", f"## {title}", ""])
                i += 1
                continue
            if line.startswith(_BULLET_SUB):
                heading = line.lstrip(_BULLET_SUB).strip()
                if heading:
                    out.extend(["", f"### {heading}", ""])
                i += 1
                continue
            if line.startswith(_BULLET_MAIN):
                item = line.lstrip(_BULLET_MAIN).strip()
                if _is_topic_heading(item):
                    out.extend(["", f"### {item.rstrip('：:')}", ""])
                elif item:
                    out.append(f"- {item}")
                i += 1
                continue
            if line.startswith("专家评语"):
                out.extend(["", "#### 专家评语再现", ""])
                i += 1
                continue
            if line == "相似度检测":
                out.extend(["", "### 相似度检测", ""])
                i += 1
                continue
            if re.match(r"^[1-9][）)]", line):
                out.append(f"- {line}")
                i += 1
                continue
            if len(line) > 4 and not re.fullmatch(r"[0-9\s]+", line):
                if _is_topic_heading(line):
                    out.extend(["", f"### {line.rstrip('：:')}", ""])
                else:
                    out.append(line)
            i += 1
    return out


def _merge_wrapped_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if not line:
            merged.append("")
            continue
        if line.startswith(("#", "-", "<!--")):
            merged.append(line)
            continue
        if merged and merged[-1] and not merged[-1].startswith(("#", "-", "<!--")):
            merged[-1] = f"{merged[-1]}{line}"
        else:
            merged.append(line)
    return merged


def convert_pdf_to_markdown(pdf_path: Path, dest_md: Path) -> Path:
    pages = _extract_pages(pdf_path)
    lines = _merge_wrapped_lines(_structure_lines(pages))
    body = "\n".join(lines).strip() + "\n"
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_md.write_text(body, encoding="utf-8")
    return dest_md


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert thesis FAQ PDF to markdown")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--out", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    if not args.pdf.is_file():
        raise SystemExit(f"PDF not found: {args.pdf}")
    out = convert_pdf_to_markdown(args.pdf, args.out)
    headings = sum(1 for l in out.read_text(encoding="utf-8").splitlines() if l.startswith("#"))
    print(f"Wrote {out} ({out.stat().st_size} bytes, ~{headings} headings)")


if __name__ == "__main__":
    main()
