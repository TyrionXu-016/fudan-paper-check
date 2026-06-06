from orchestrator.export_doc import _wrap_pdf_text, export_pdf_bytes, export_markdown
from schema.models import PreviewSpan, PreviewView


def test_export_pdf_non_empty():
    preview = PreviewView(
        task_id="t1",
        paper_title="测试论文",
        spans=[
            PreviewSpan(span_id="s1", section_id="sec1", text="第一段内容。"),
            PreviewSpan(span_id="s2", section_id="sec1", text="第二段内容。"),
        ],
    )
    pdf = export_pdf_bytes(preview)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 100


def test_export_markdown_highlights():
    preview = PreviewView(
        task_id="t1",
        paper_title="标题",
        spans=[
            PreviewSpan(span_id="s1", section_id="sec1", text="改后", highlight="accepted"),
        ],
    )
    md = export_markdown(preview)
    assert "改后 ✓" in md


def test_pdf_text_wrap_keeps_long_content():
    text = "复旦大学论文格式预检系统" * 20
    lines = _wrap_pdf_text(text, "Helvetica", 11, 120)
    assert "".join(lines) == text
    assert len(lines) > 1
