from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from worker.converter import PDFConverter

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tiff", ".webp", ".tif"}
ARCHIVE_SUFFIXES = {".zip"}


class MseDocumentConverter:
    """Convert MSE uploads (PDF / image / zip) to maker + mineru markdown."""

    def __init__(self) -> None:
        self.pdf_converter = PDFConverter()

    def convert(self, input_path: Path, out_dir: Path) -> tuple[Path, Path | None]:
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = input_path.suffix.lower()
        if suffix == ".pdf":
            return self.pdf_converter.convert(input_path, out_dir)
        if suffix in IMAGE_SUFFIXES:
            return self._convert_images([input_path], out_dir)
        if suffix in ARCHIVE_SUFFIXES:
            return self._convert_zip(input_path, out_dir)
        raise ValueError(f"unsupported file type: {suffix}")

    def _convert_zip(self, zip_path: Path, out_dir: Path) -> tuple[Path, Path | None]:
        extract_dir = out_dir / "_zip_extract"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        images = sorted(
            p
            for p in extract_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        )
        if not images:
            raise ValueError("zip contains no supported images")
        return self._convert_images(images, out_dir)

    def _convert_images(
        self,
        images: list[Path],
        out_dir: Path,
    ) -> tuple[Path, Path | None]:
        maker_out = out_dir / "paper_maker.md"
        mineru_out = out_dir / "paper_mineru.md"
        assets_dir = out_dir / "images"
        assets_dir.mkdir(exist_ok=True)

        maker_lines: list[str] = ["# 上传论文（图片源）", ""]
        mineru_lines: list[str] = []

        for idx, src in enumerate(images):
            page = idx
            dest = assets_dir / f"page_{idx + 1:03d}{src.suffix.lower()}"
            shutil.copy2(src, dest)
            rel = f"images/{dest.name}"

            maker_lines.append(f"![](_page_{page}_Picture_0.jpeg)")
            maker_lines.append(f"![]({rel})")
            maker_lines.append("")
            mineru_lines.append(f"<!-- page: {page + 1} -->")
            mineru_lines.append(f"![]({rel})")
            mineru_lines.append("")

        maker_out.write_text("\n".join(maker_lines), encoding="utf-8")
        mineru_out.write_text("\n".join(mineru_lines), encoding="utf-8")
        return maker_out, mineru_out
