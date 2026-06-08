from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path


class PDFConverter:
    """Convert PDFs with real Maker/MinerU-compatible converter images."""

    def __init__(self) -> None:
        self.maker_image = os.getenv("MAKER_IMAGE", "fudan-pager-mse-maker")
        self.mineru_image = os.getenv("MINERU_IMAGE", "").strip()
        self.mode = os.getenv("PDF_CONVERTER_MODE", "docker").strip().lower()

    def convert(self, pdf_path: Path, out_dir: Path) -> tuple[Path, Path | None]:
        out_dir.mkdir(parents=True, exist_ok=True)
        maker_out = out_dir / "paper_maker.md"
        mineru_out = out_dir / "paper_mineru.md"

        if self.mode != "docker":
            raise RuntimeError(
                "PDF_CONVERTER_MODE must be docker for PDF uploads; "
                "upload maker/mineru markdown if converters are unavailable"
            )
        if not shutil.which("docker"):
            raise RuntimeError("docker CLI is required in worker container for PDF conversion")

        self._docker_convert(pdf_path, out_dir, maker_out, mineru_out)
        if not maker_out.exists() or maker_out.stat().st_size == 0:
            raise RuntimeError(f"maker converter produced no output: {maker_out}")

        mineru = mineru_out if mineru_out.exists() and mineru_out.stat().st_size > 0 else None
        return maker_out, mineru

    def _docker_convert(
        self, pdf_path: Path, out_dir: Path, maker_out: Path, mineru_out: Path
    ) -> None:
        pdf_abs = pdf_path.resolve()
        out_abs = out_dir.resolve()
        volume_args, input_arg, maker_output_arg, mineru_output_arg = self._docker_paths(
            pdf_abs, out_abs, maker_out.resolve(), mineru_out.resolve()
        )

        self._run_converter(
            "maker",
            self.maker_image,
            volume_args,
            input_arg,
            maker_output_arg,
            required=True,
        )
        if self.mineru_image:
            self._run_converter(
                "mineru",
                self.mineru_image,
                volume_args,
                input_arg,
                mineru_output_arg,
                required=False,
            )

    @staticmethod
    def _docker_paths(
        pdf_abs: Path, out_abs: Path, maker_out: Path, mineru_out: Path
    ) -> tuple[list[str], str, str, str]:
        if Path("/.dockerenv").exists():
            container_id = socket.gethostname()
            return ["--volumes-from", container_id], str(pdf_abs), str(maker_out), str(mineru_out)
        return (
            ["-v", f"{pdf_abs.parent}:/input:ro", "-v", f"{out_abs}:/output"],
            f"/input/{pdf_abs.name}",
            "/output/paper_maker.md",
            "/output/paper_mineru.md",
        )

    @staticmethod
    def _run_converter(
        label: str,
        image: str,
        volume_args: list[str],
        input_arg: str,
        output_arg: str,
        *,
        required: bool,
    ) -> None:
        cmd = [
            "docker",
            "run",
            "--rm",
            *volume_args,
            image,
            input_arg,
            output_arg,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
            stderr = getattr(exc, "stderr", "") or str(exc)
            if not required:
                print(
                    f"{label} converter failed for optional image {image}; "
                    f"continuing without optional output: {stderr}",
                    flush=True,
                )
                return
            raise RuntimeError(f"{label} converter failed for image {image}: {stderr}") from exc
