#!/usr/bin/env bash
# Download a public CS master's thesis PDF for local quasi-production MinerU tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAGE_URL="${MSE_PUBLIC_THESIS_PAGE_URL:-https://digitalcommons.dartmouth.edu/masters_theses/24/}"
OUT="${MINERU_TEST_PDF:-$ROOT/samples/real_pdfs/public_cs_master_thesis.pdf}"

python3 - "$PAGE_URL" "$OUT" "$ROOT" <<'PY'
from __future__ import annotations

import html
import re
import sys
import urllib.request
from pathlib import Path

page_url = sys.argv[1]
out = Path(sys.argv[2])
root = Path(sys.argv[3])
sys.path.insert(0, str(root / "packages"))

from mse.public_thesis import validate_public_thesis_pdf

out.parent.mkdir(parents=True, exist_ok=True)


if out.exists():
    validation = validate_public_thesis_pdf(out)
    if validation.ready:
        print(out)
        raise SystemExit(0)
    raise SystemExit(f"existing PDF does not look like the Dartmouth thesis: {out}: {validation.reason}")

request = urllib.request.Request(page_url, headers={"User-Agent": "fudan-pager-check/1.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    page = response.read().decode("utf-8", errors="ignore")

match = re.search(r'name="bepress_citation_pdf_url"\s+content="([^"]+)"', page)
if not match:
    match = re.search(r'href="([^"]*viewcontent\.cgi[^"]*)"', page)
if not match:
    raise SystemExit(f"could not find PDF URL in {page_url}")

pdf_url = html.unescape(match.group(1))
tmp = out.with_suffix(out.suffix + ".tmp")
try:
    pdf_request = urllib.request.Request(
        pdf_url,
        headers={
            "User-Agent": "Mozilla/5.0 (fudan-pager-check/1.0)",
            "Referer": page_url,
        },
    )
    with urllib.request.urlopen(pdf_request, timeout=120) as response, tmp.open("wb") as f:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
except Exception as exc:
    tmp.unlink(missing_ok=True)
    raise SystemExit(f"could not download Dartmouth thesis PDF from {pdf_url}: {exc}")

validation = validate_public_thesis_pdf(tmp)
if not validation.ready:
    tmp.unlink(missing_ok=True)
    raise SystemExit(f"could not download Dartmouth thesis PDF: {validation.reason}: {pdf_url}")

tmp.replace(out)
print(out)
PY
