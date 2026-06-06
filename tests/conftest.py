import os
import sys
from pathlib import Path

os.environ.setdefault("JOB_RUN_INLINE", "1")
os.environ["NOTIFIER"] = "console"
os.environ["LLM_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ.setdefault("MSE_ALLOW_MOCK_FALLBACK", "1")
os.environ.setdefault("PDF_CONVERTER_MODE", "mock")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps"))
