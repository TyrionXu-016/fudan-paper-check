from __future__ import annotations

import zipfile
from pathlib import Path

from worker.mse_converter import MseDocumentConverter


def test_convert_single_image(tmp_path):
    img = tmp_path / "page1.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    out = tmp_path / "out"
    maker, mineru = MseDocumentConverter().convert(img, out)
    assert maker.exists()
    assert mineru and mineru.exists()
    text = maker.read_text(encoding="utf-8")
    assert "_page_0_" in text
    assert (out / "images").exists()


def test_convert_zip_images(tmp_path):
    zpath = tmp_path / "pages.zip"
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    img1.write_bytes(b"\xff\xd8\xff")
    img2.write_bytes(b"\xff\xd8\xff")
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.write(img1, "a.jpg")
        zf.write(img2, "b.jpg")
    out = tmp_path / "out"
    maker, mineru = MseDocumentConverter().convert(zpath, out)
    assert maker.read_text(encoding="utf-8").count("_page_") >= 2
    assert mineru and "<!-- page:" in mineru.read_text(encoding="utf-8")
