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
        self.mineru_backend = os.getenv("MINERU_BACKEND", "pipeline")
        self.mineru_method = os.getenv("MINERU_METHOD", "auto")
        self.use_docker = use_docker_converter()
        self.allow_mock = allow_mock_fallback()
        self.max_retries = int(os.getenv("MINERU_MAX_RETRIES", "2"))
        self.maker_timeout = int(os.getenv("MAKER_TIMEOUT_SECONDS", "300"))
        self.mineru_timeout = int(os.getenv("MINERU_TIMEOUT_SECONDS", "1800"))
        self.mineru_start_page = os.getenv("MINERU_START_PAGE", "").strip()
        self.mineru_end_page = os.getenv("MINERU_END_PAGE", "").strip()
        self.maker_start_page = os.getenv("MAKER_START_PAGE", self.mineru_start_page).strip()
        self.maker_end_page = os.getenv("MAKER_END_PAGE", self.mineru_end_page).strip()
        self.mineru_docker_shm_size = os.getenv("MINERU_DOCKER_SHM_SIZE", "").strip()
        self.mineru_extra_env = {
            key: value.strip()
            for key in (
                "MINERU_PDF_RENDER_THREADS",
                "MINERU_PROCESSING_WINDOW_SIZE",
                "MINERU_FORMULA_ENABLE",
                "MINERU_TABLE_ENABLE",
                "MINERU_TABLE_MERGE_ENABLE",
            )
            if (value := os.getenv(key, "").strip())
        }
        cache_dir = os.getenv("MINERU_CACHE_DIR", "").strip()
        self.mineru_cache_dir = Path(cache_dir) if cache_dir else None
        self.mineru_cache_volume = os.getenv("MINERU_CACHE_VOLUME", "fudan-pager-mineru-cache")
        self.container_data_root = Path(os.getenv("DOCKER_CONTAINER_DATA_ROOT", "/app/data")).resolve()
        host_data_root = os.getenv("DOCKER_HOST_DATA_ROOT", "").strip()
        self.host_data_root = Path(host_data_root).resolve() if host_data_root else None

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
                if not mineru_out.exists():
                    if not self.allow_mock:
                        raise RuntimeError("MinerU conversion produced no markdown")
                else:
                    self._validate_markdown(mineru_out, "MinerU", required=not self.allow_mock)
                if not maker_out.exists():
                    if mineru_out.exists():
                        shutil.copy(mineru_out, maker_out)
                    else:
                        raise RuntimeError("PDF conversion produced no maker markdown")
                self._validate_markdown(maker_out, "Maker", required=not self.allow_mock)
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
        pdf_mount = self._host_mount_path(pdf_abs.parent)
        out_mount = self._host_mount_path(out_abs)
        if self.mineru_cache_dir is not None:
            self.mineru_cache_dir.mkdir(parents=True, exist_ok=True)
            cache_mount = f"{self.mineru_cache_dir.resolve()}:/root/.cache"
        else:
            cache_mount = f"{self.mineru_cache_volume}:/root/.cache"
        mineru_docker_prefix = ["docker", "run", "--rm"]
        if self.mineru_docker_shm_size:
            mineru_docker_prefix.extend(["--shm-size", self.mineru_docker_shm_size])
        mineru_env = [
            "HF_HOME=/root/.cache/huggingface",
            "MODELSCOPE_CACHE=/root/.cache/modelscope",
            f"MINERU_BACKEND={self.mineru_backend}",
            f"MINERU_METHOD={self.mineru_method}",
        ]
        if self.mineru_start_page:
            mineru_env.append(f"MINERU_START_PAGE={self.mineru_start_page}")
        if self.mineru_end_page:
            mineru_env.append(f"MINERU_END_PAGE={self.mineru_end_page}")
        for key, value in self.mineru_extra_env.items():
            mineru_env.append(f"{key}={value}")
        mineru_env_args = [arg for env in mineru_env for arg in ("-e", env)]
        maker_env = []
        if self.maker_start_page:
            maker_env.append(f"MAKER_START_PAGE={self.maker_start_page}")
        if self.maker_end_page:
            maker_env.append(f"MAKER_END_PAGE={self.maker_end_page}")
        maker_env_args = [arg for env in maker_env for arg in ("-e", env)]
        cmds: list[tuple[list[str], int]] = [
            ([
                "docker",
                "run",
                "--rm",
                "-v",
                f"{pdf_mount}:/input:ro",
                "-v",
                f"{out_mount}:/output",
                *maker_env_args,
                self.maker_image,
                f"/input/{pdf_abs.name}",
                "/output/paper_maker.md",
            ], self.maker_timeout),
            (mineru_docker_prefix + [
                "-v",
                f"{pdf_mount}:/input:ro",
                "-v",
                f"{out_mount}:/output",
                "-v",
                cache_mount,
                *mineru_env_args,
                self.mineru_image,
                f"/input/{pdf_abs.name}",
                "/output/paper_mineru.md",
            ], self.mineru_timeout),
        ]
        errors: list[str] = []
        for cmd, timeout in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
                errors.append(str(exc))

        if not mineru_out.exists() and not self.allow_mock:
            detail = "; ".join(errors) if errors else "mineru output missing"
            raise RuntimeError(f"MinerU docker conversion failed: {detail}")
        if not maker_out.exists():
            if mineru_out.exists():
                shutil.copy(mineru_out, maker_out)
            elif self.allow_mock:
                self._mock_convert(pdf_path, maker_out, mineru_out)
                return
            else:
                detail = "; ".join(errors) if errors else "maker output missing"
                raise RuntimeError(f"PDF docker conversion failed: {detail}")

    def _host_mount_path(self, path: Path) -> Path:
        if self.host_data_root is None:
            return path
        try:
            relative = path.resolve().relative_to(self.container_data_root)
        except ValueError:
            return path
        return self.host_data_root / relative

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

    @staticmethod
    def _validate_markdown(path: Path, label: str, *, required: bool) -> None:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if required and not text.strip():
            raise RuntimeError(f"{label} conversion produced empty markdown")
        lowered = text.lower()
        if required and (
            "converted by maker stub" in lowered
            or "converted by mineru stub" in lowered
            or "replace this stub" in lowered
        ):
            raise RuntimeError(f"{label} conversion produced stub markdown")
