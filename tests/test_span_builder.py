from parser.span_builder import build_spans
from parser.fusion import DualSourceFusionParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def test_build_spans_from_sample():
    maker = SAMPLES / "基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md"
    doc = DualSourceFusionParser().parse_files(maker, None)
    spans = build_spans(doc)
    assert spans
    assert all(s.id and s.text for s in spans)
    assert all(s.start_offset <= s.end_offset for s in spans)
