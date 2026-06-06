#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mse.sample_manifest import validate_sample_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local MSE thesis sample manifest.")
    parser.add_argument(
        "--manifest",
        default=str(Path(__file__).resolve().parents[1] / "samples" / "mse" / "manifest.yaml"),
    )
    parser.add_argument("--require-primary", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate_sample_manifest(args.manifest, require_primary=args.require_primary)
    payload = {
        "manifest": str(result.manifest_path),
        "entries": [entry.__dict__ for entry in result.entries],
        "primary_ready_count": result.primary_ready_count,
        "ready": result.ready,
        "missing": result.missing,
        "invalid": result.invalid,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif result.ready:
        print(f"OK: {result.primary_ready_count} primary MSE sample(s) ready")
    else:
        print("CONFIG_REQUIRED: local CNKI/private MSE samples are not ready")
        for item in result.missing:
            print(f"MISSING: {item}")
        for item in result.invalid:
            print(f"INVALID: {item}")
    return 0 if result.ready or not args.require_primary else 2


if __name__ == "__main__":
    sys.exit(main())
