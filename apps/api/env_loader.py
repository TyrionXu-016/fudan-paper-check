"""Load repo-root `.env` and ensure `packages` / `apps` are on sys.path."""
from __future__ import annotations

import sys
from pathlib import Path


def bootstrap() -> None:
    root = Path(__file__).resolve().parents[2]
    for sub in ("packages", "apps"):
        path = root / sub
        entry = str(path)
        if path.is_dir() and entry not in sys.path:
            sys.path.insert(0, entry)

    env_file = root / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_file, override=False)


bootstrap()
