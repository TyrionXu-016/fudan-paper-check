from __future__ import annotations

from mse.issue_merger import merge_issues
from rag.mse_rule_index import build_project_index, load_project_index
from schema.models import CheckCategory, Issue, IssueSeverity


def test_merge_issues_dedupes():
    a = Issue(code="X", category=CheckCategory.FORMAT, severity=IssueSeverity.WARNING, message="m")
    b = Issue(code="X", category=CheckCategory.FORMAT, severity=IssueSeverity.ERROR, message="m")
    merged = merge_issues([a], [b])
    assert len(merged) == 1
    assert merged[0].severity == IssueSeverity.ERROR


def test_build_project_index(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.mse_rule_index._MSE_INDEX_ROOT", tmp_path / "mse")
    path = build_project_index("proj-1", include_default=True)
    assert path.exists()
    data = load_project_index("proj-1")
    assert data is not None
    assert data["chunk_count"] >= 1
