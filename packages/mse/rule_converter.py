from __future__ import annotations

import tempfile
from pathlib import Path

from mse.settings import allow_mock_fallback

RULE_ALLOWED_SUFFIXES = {".md", ".docx", ".pdf"}
MAX_RULE_BYTES = 20 * 1024 * 1024


def _docx_to_markdown(src: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("python-docx is required for docx rule upload") from exc

    doc = Document(str(src))
    lines: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            lines.append("")
            continue
        style = (para.style.name or "").lower()
        if "heading 1" in style or style == "title":
            lines.append(f"# {text}")
        elif "heading 2" in style:
            lines.append(f"## {text}")
        elif "heading 3" in style:
            lines.append(f"### {text}")
        else:
            lines.append(text)
    body = "\n".join(lines).strip()
    if not body:
        raise ValueError("docx contains no extractable text")
    return body + "\n"


def _pdf_to_markdown(src: Path, work_dir: Path) -> str:
    from worker.converter import PDFConverter

    if not allow_mock_fallback():
        import shutil as sh

        if not sh.which("docker"):
            raise RuntimeError("PDF rule upload requires docker when MSE_ALLOW_MOCK_FALLBACK=0")

    converter = PDFConverter()
    maker, mineru = converter.convert(src, work_dir)
    pick = mineru if mineru and mineru.exists() else maker
    text = pick.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("pdf conversion produced empty markdown")
    return text + "\n"


def convert_rule_to_markdown(src: Path, dest_md: Path) -> Path:
    """Normalize uploaded rule document to markdown at dest_md."""
    suffix = src.suffix.lower()
    if suffix not in RULE_ALLOWED_SUFFIXES:
        raise ValueError(f"unsupported rule type: {suffix}")

    dest_md.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".md":
        raw = src.read_text(encoding="utf-8").strip()
        if not raw:
            raise ValueError("markdown file is empty")
        dest_md.write_text(raw + "\n", encoding="utf-8")
        return dest_md

    if suffix == ".docx":
        dest_md.write_text(_docx_to_markdown(src), encoding="utf-8")
        return dest_md

    with tempfile.TemporaryDirectory(prefix="mse-rule-pdf-") as tmp:
        work = Path(tmp)
        dest_md.write_text(_pdf_to_markdown(src, work), encoding="utf-8")
    return dest_md
