from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PUBLIC_THESIS_PDF_PATH = (
    Path(__file__).resolve().parents[2] / "samples" / "real_pdfs" / "public_cs_master_thesis.pdf"
)
EXPECTED_PUBLIC_THESIS_MARKERS = (
    "chinese font style transfer",
    "xue hanyu",
    "dartmouth",
)


@dataclass(frozen=True)
class PublicThesisValidation:
    path: Path
    ready: bool
    reason: str = ""


def validate_public_thesis_pdf(path: str | Path) -> PublicThesisValidation:
    pdf_path = Path(path)
    if not pdf_path.exists():
        return PublicThesisValidation(pdf_path, False, "PDF is missing")
    if pdf_path.read_bytes()[:4] != b"%PDF":
        return PublicThesisValidation(pdf_path, False, "file is not a PDF")
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        text_parts = []
        for page in reader.pages[:5]:
            text_parts.append(page.extract_text() or "")
        text = re.sub(r"\s+", " ", "\n".join(text_parts).lower())
    except Exception as exc:
        return PublicThesisValidation(
            pdf_path,
            False,
            f"could not extract PDF text with pypdf: {exc}",
        )
    missing = [marker for marker in EXPECTED_PUBLIC_THESIS_MARKERS if marker not in text]
    if missing:
        return PublicThesisValidation(
            pdf_path,
            False,
            "does not look like the Dartmouth thesis; missing expected marker(s): "
            + ", ".join(missing),
        )
    return PublicThesisValidation(pdf_path, True)
