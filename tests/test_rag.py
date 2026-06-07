import uuid

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
    assert "fudan_university" in ids
    assert "scut_natural_science" in ids


def test_fudan_index_retrieves_school_rules(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)

    path = build_index("fudan_university")
    assert path.exists()
    result = retrieve_rules("fudan_university", "复旦 摘要 关键词 图表公式", top_k=5)
    assert result.rule_base_id == "fudan_university"
    assert result.results
    assert any("复旦" in item.text or "关键词" in item.text for item in result.results)


def test_fudan_thesis_index_retrieves_yaml_rules(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)

    path = build_index("fudan_thesis")
    assert path.exists()
    index = load_index("fudan_thesis")
    assert index is not None
    assert index["chunk_count"] >= 30

    binding = retrieve_rules("fudan_thesis", "不能使用钉子装订", top_k=5)
    assert binding.rule_base_id == "fudan_thesis"
    assert any("不能使用钉子装订" in item.text for item in binding.results)

    cover = retrieve_rules("fudan_thesis", "封面 学校代码 10246 十一项", top_k=5)
    assert any("学校代码（10246）" in item.text for item in cover.results)


def _auth_headers(client):
    email = f"rag_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/v1/auth/register",
        json={"email": email, "password": "secret12", "name": "Rag Tester"},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_retrieve_api_requires_auth(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)
    build_index("generic")
    client = TestClient(app)
    unauth = client.get(
        "/v1/rule_bases/generic/retrieve",
        params={"q": "摘要 关键词", "top_k": 2},
    )
    assert unauth.status_code == 401

    res = client.get(
        "/v1/rule_bases/generic/retrieve",
        headers=_auth_headers(client),
        params={"q": "摘要 关键词", "top_k": 2},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 0
    assert body["data"]["results"]


def test_retrieve_api_returns_503_when_index_missing(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from api.main import app

    monkeypatch.setattr("rag.rule_index._INDEX_DIR", tmp_path)
    client = TestClient(app)
    res = client.get(
        "/v1/rule_bases/generic/retrieve",
        headers=_auth_headers(client),
        params={"q": "摘要 关键词", "top_k": 2},
    )
    assert res.status_code == 503
    assert res.json()["code"] == "RAG_INDEX_NOT_READY"
