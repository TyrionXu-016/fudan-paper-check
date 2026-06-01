from __future__ import annotations

from parser.fusion import DualSourceFusionParser
from parser.page_mapper import PageMapper


def test_page_mapper_from_maker_image_paths():
    parser = DualSourceFusionParser()
    sample = "samples/基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    doc = parser.parse_files(sample, None)
    mapper = PageMapper.from_document(doc, maker_path=sample)
    assert mapper.page_for_line(1) is not None
    page_high = mapper.page_for_line(400)
    assert page_high is not None
    assert page_high >= mapper.page_for_line(1)


def test_page_line_label():
    mapper = PageMapper({10: 3, 20: 5})
    assert mapper.page_line_label(3, 10) == "第 3 页（约第 10 行）"
    assert mapper.page_line_label(5, None) == "第 5 页"
