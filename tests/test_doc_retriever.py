import pytest
from rag.doc_index import build_task_index, drop_task_index, _task_index_path
from rag.doc_retriever import retrieve_context
from schema.models import PaperDocument, PaperMeta, Span, Section, SectionKind


def test_build_and_retrieve_context(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.doc_index._TASKS_DIR", tmp_path)
    
    doc = PaperDocument(
        meta=PaperMeta(title="Test Paper"),
        sections=[
            Section(id="sec1", kind=SectionKind.INTRO, title="Intro", start_line=1, end_line=10)
        ]
    )
    
    spans = [
        Span(id="span1", section_id="sec1", block_id="b1", start_offset=0, end_offset=10, text="first span"),
        Span(id="span2", section_id="sec1", block_id="b2", start_offset=11, end_offset=20, text="second span"),
        Span(id="span3", section_id="sec1", block_id="b3", start_offset=21, end_offset=30, text="third span")
    ]
    
    task_id = "test_task_123"
    
    # Test build index
    index_path = build_task_index(task_id, doc, spans)
    assert index_path.exists()
    assert index_path == _task_index_path(task_id)
    
    # Test retrieve context
    snippets = retrieve_context(task_id, "span2", window=2)
    assert len(snippets) > 0
    span_ids = [s.span_id for s in snippets]
    assert "span2" in span_ids
    assert "span1" in span_ids # neighbor
    assert "span3" in span_ids # neighbor
    
    # Test drop index
    drop_task_index(task_id)
    assert not index_path.exists()

def test_retrieve_missing_index(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.doc_index._TASKS_DIR", tmp_path)
    # Task index doesn't exist
    snippets = retrieve_context("missing_task", "span1")
    assert snippets == []
