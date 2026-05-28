import os
import sys
from pathlib import Path

os.environ.setdefault("JOB_RUN_INLINE", "1")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps"))
