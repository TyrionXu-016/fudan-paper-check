from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from mse.settings import allow_mock_fallback, use_docker_converter


class PDFConverter:
    """Convert PDF via Maker and MinerU containers or local CLI fallback."""

    def __init__(self) -> None:
        self.maker_image = os.getenv("MAKER_IMAGE", "maker-pdf:latest")
        self.mineru_image = os.getenv("MINERU_IMAGE", "mineru:latest")
        self.use_docker = use_docker_converter()
        self.allow_mock = allow_mock_fallback()
        self.max_retries = int(os.getenv("MINERU_MAX_RETRIES", "2"))

    def convert(self, pdf_path: Path, out_dir: Path) -> tuple[Path, Path | None]:
        out_dir.mkdir(parents=True, exist_ok=True)
        maker_out = out_dir / "paper_maker.md"
        mineru_out = out_dir / "paper_mineru.md"

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                if self.use_docker and shutil.which("docker"):
                    self._docker_convert(pdf_path, out_dir, maker_out, mineru_out)
                elif self.allow_mock:
                    self._mock_convert(pdf_path, maker_out, mineru_out)
                else:
                    raise RuntimeError(
                        "PDF conversion requires docker (PDF_CONVERTER_MODE=docker) "
                        "or MSE_ALLOW_MOCK_FALLBACK=1 for local dev"
                    )
                if not maker_out.exists():
                    raise RuntimeError("PDF conversion produced no maker markdown")
                mineru = mineru_out if mineru_out.exists() else None
                return maker_out, mineru
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2**attempt)
        raise last_error or RuntimeError("PDF conversion failed")

    def _docker_convert(
        self, pdf_path: Path, out_dir: Path, maker_out: Path, mineru_out: Path
    ) -> None:
        pdf_abs = pdf_path.resolve()
        out_abs = out_dir.resolve()
        cmds = [
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{pdf_abs.parent}:/input:ro",
                "-v",
                f"{out_abs}:/output",
                self.maker_image,
                f"/input/{pdf_abs.name}",
                "/output/paper_maker.md",
            ],
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{pdf_abs.parent}:/input:ro",
                "-v",
                f"{out_abs}:/output",
                self.mineru_image,
                f"/input/{pdf_abs.name}",
                "/output/paper_mineru.md",
            ],
        ]
        errors: list[str] = []
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
                errors.append(str(exc))

        if not maker_out.exists():
            if self.allow_mock:
                self._mock_convert(pdf_path, maker_out, mineru_out)
                return
            detail = "; ".join(errors) if errors else "maker output missing"
            raise RuntimeError(f"PDF docker conversion failed: {detail}")

    @staticmethod
    def _mock_convert(pdf_path: Path, maker_out: Path, mineru_out: Path) -> None:
        """Fallback: copy bundled samples when converter unavailable."""
        root = Path(__file__).resolve().parents[2]
        samples = root / "samples"
        maker_sample = next(root.glob("*_maker.md"), None) or samples / "paper_maker.md"
        mineru_sample = next(root.glob("*_mineru.md"), None) or samples / "paper_mineru.md"
        if maker_sample.exists():
            shutil.copy(maker_sample, maker_out)
        else:
            maker_out.write_text(f"# Converted from {pdf_path.name}\n", encoding="utf-8")
        if mineru_sample.exists():
            shutil.copy(mineru_sample, mineru_out)
