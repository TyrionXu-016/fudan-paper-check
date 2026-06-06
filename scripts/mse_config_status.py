#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mse.config_status import DEFAULT_MANIFEST_PATH, build_config_status, load_status_env
from mse.public_thesis import DEFAULT_PUBLIC_THESIS_PDF_PATH


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Check MSE local quasi-production configuration status.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument(
        "--public-pdf",
        default=str(DEFAULT_PUBLIC_THESIS_PDF_PATH),
        help="Dartmouth public thesis PDF to validate. Defaults to samples/real_pdfs/public_cs_master_thesis.pdf.",
    )
    parser.add_argument(
        "--env-file",
        action="append",
        default=None,
        help="Env file to merge after the current environment. Defaults to .env when present.",
    )
    parser.add_argument("--no-env-file", action="store_true")
    parser.add_argument(
        "--quasi-prod-only",
        action="store_true",
        help="Only require the checks used by mse_acceptance_quasi_prod.sh.",
    )
    parser.add_argument("--skip-quasi-prod", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    env_files = [] if args.no_env_file else (args.env_file or [root / ".env"])
    status = build_config_status(
        manifest_path=args.manifest,
        public_pdf_path=args.public_pdf,
        env=load_status_env(env_files),
        require_private_samples=not args.quasi_prod_only,
        require_webhook=not args.quasi_prod_only,
        require_quasi_prod=not args.skip_quasi_prod,
    )

    if args.json:
        print(json.dumps(status.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for check in status.checks:
            prefix = "READY" if check.status == "ready" else "CONFIG_REQUIRED"
            print(f"{prefix}: {check.id} - {check.label}")
            for detail in check.details:
                print(f"  - {detail}")
        if status.ready:
            print("OK: MSE local configuration is ready")
        else:
            print("CONFIG_REQUIRED: MSE local configuration is incomplete")
    return 0 if status.ready else 2


if __name__ == "__main__":
    sys.exit(main())
