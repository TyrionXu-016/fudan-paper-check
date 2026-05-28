from rag.rule_index import build_all_indexes, build_index, load_index
from rag.rule_retriever import retrieve_rules


def test_build_index_and_retrieve(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)

    path = build_index("generic")
    assert path.exists()
    index = load_index("generic")
    assert index is not None
    assert index["chunk_count"] > 0

    result = retrieve_rules("generic", "参考文献 GB/T 7714", top_k=3)
    assert result.rule_base_id == "generic"
    assert result.results
    assert any("reference" in item.dimension or "7714" in item.text for item in result.results)


def test_build_all_indexes(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)
    paths = build_all_indexes()
    assert len(paths) >= 2
    ids = {p.stem for p in paths}
    assert "generic" in ids
    assert "scut_natural_science" in ids


def test_retrieve_api():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    res = client.get(
        "/v1/rule_bases/generic/retrieve",
        params={"q": "摘要 关键词", "top_k": 2},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["results"]
