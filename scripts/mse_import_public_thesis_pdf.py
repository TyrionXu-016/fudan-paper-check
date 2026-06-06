#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))

from mse.public_thesis import DEFAULT_PUBLIC_THESIS_PDF_PATH, validate_public_thesis_pdf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and import the Dartmouth public thesis PDF used by MSE quasi-prod."
    )
    parser.add_argument("source", help="Downloaded Dartmouth thesis PDF")
    parser.add_argument("--target", default=str(DEFAULT_PUBLIC_THESIS_PDF_PATH))
    args = parser.parse_args()

    source = Path(args.source)
    target = Path(args.target)
    validation = validate_public_thesis_pdf(source)
    if not validation.ready:
        print(f"CONFIG_REQUIRED: source PDF is not the expected Dartmouth thesis: {validation.reason}")
        print("Download from https://digitalcommons.dartmouth.edu/masters_theses/24/ and retry.")
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    shutil.copy2(source, tmp)
    tmp.replace(target)
    print(f"OK: imported Dartmouth public thesis PDF to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
