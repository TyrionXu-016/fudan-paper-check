from __future__ import annotations

import os
import socket
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
        docker_kwargs, input_arg, maker_output_arg, mineru_output_arg = self._docker_paths(
            pdf_abs, out_abs, maker_out.resolve(), mineru_out.resolve()
        )
        client = self._docker_client()

        self._run_converter(
            "maker",
            self.maker_image,
            docker_kwargs,
            input_arg,
            maker_output_arg,
            client=client,
            required=True,
        )
        if self.mineru_image:
            self._run_converter(
                "mineru",
                self.mineru_image,
                docker_kwargs,
                input_arg,
                mineru_output_arg,
                client=client,
                required=False,
            )

    @staticmethod
    def _docker_paths(
        pdf_abs: Path, out_abs: Path, maker_out: Path, mineru_out: Path
    ) -> tuple[dict[str, object], str, str, str]:
        if Path("/.dockerenv").exists():
            container_id = socket.gethostname()
            return {"volumes_from": [container_id]}, str(pdf_abs), str(maker_out), str(mineru_out)
        return (
            {
                "volumes": {
                    str(pdf_abs.parent): {"bind": "/input", "mode": "ro"},
                    str(out_abs): {"bind": "/output", "mode": "rw"},
                }
            },
            f"/input/{pdf_abs.name}",
            "/output/paper_maker.md",
            "/output/paper_mineru.md",
        )

    @staticmethod
    def _docker_client():
        try:
            import docker
        except ImportError as exc:
            raise RuntimeError("docker Python SDK is required for PDF conversion") from exc
        if not hasattr(docker, "from_env"):
            raise RuntimeError("docker Python SDK is required for PDF conversion")
        try:
            return docker.from_env()
        except Exception as exc:
            raise RuntimeError("cannot connect to Docker daemon for PDF conversion") from exc

    @staticmethod
    def _run_converter(
        label: str,
        image: str,
        docker_kwargs: dict[str, object],
        input_arg: str,
        output_arg: str,
        *,
        client,
        required: bool,
    ) -> None:
        try:
            client.containers.run(
                image,
                [input_arg, output_arg],
                remove=True,
                stdout=True,
                stderr=True,
                detach=False,
                **docker_kwargs,
            )
        except Exception as exc:
            detail = str(exc)
            if not required:
                print(
                    f"{label} converter failed for optional image {image}; "
                    f"continuing without optional output: {detail}",
                    flush=True,
                )
                return
            raise RuntimeError(f"{label} converter failed for image {image}: {detail}") from exc
