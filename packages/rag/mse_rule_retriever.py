from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, Field

from rag.mse_rule_index import build_project_index, load_project_index
from rag.rule_retriever import _bm25_score, _substring_score, _tokenize


class ProjectRuleSnippet(BaseModel):
    id: str
    dimension: str
    text: str
    score: float
    source: str


class RetrieveProjectRulesResponse(BaseModel):
    project_id: str
    query: str
    results: list[ProjectRuleSnippet] = Field(default_factory=list)


def retrieve_project_rules(
    project_id: str,
    query: str,
    *,
    top_k: int = 5,
    journal_profile: str | None = None,
) -> RetrieveProjectRulesResponse:
    index = load_project_index(project_id)
    if index is None:
        build_project_index(project_id)
        index = load_project_index(project_id)

    chunks: list[dict] = []
    if index:
        chunks.extend(index.get("chunks") or [])

    if journal_profile:
        from rag.rule_retriever import retrieve_rules

        journal = retrieve_rules(journal_profile, query, top_k=top_k)
        for item in journal.results:
            chunks.append(
                {
                    "id": item.id,
                    "dimension": item.dimension,
                    "text": item.text,
                    "source": item.source,
                }
            )

    if not chunks:
        return RetrieveProjectRulesResponse(project_id=project_id, query=query, results=[])

    query_tokens = _tokenize(query)
    tokenized_docs = [_tokenize(c.get("text", "")) for c in chunks]
    n_docs = max(len(tokenized_docs), 1)
    avg_dl = sum(len(doc) for doc in tokenized_docs) / n_docs
    df: Counter = Counter()
    for doc in tokenized_docs:
        df.update(set(doc))

    scored: list[ProjectRuleSnippet] = []
    for chunk, doc_tokens in zip(chunks, tokenized_docs):
        text = chunk.get("text", "")
        score = _bm25_score(query_tokens, doc_tokens, avg_dl, df, n_docs)
        score = max(score, _substring_score(query, text))
        if score <= 0:
            continue
        scored.append(
            ProjectRuleSnippet(
                id=chunk["id"],
                dimension=chunk.get("dimension", ""),
                text=chunk.get("text", ""),
                score=round(score, 4),
                source=chunk.get("source", ""),
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    return RetrieveProjectRulesResponse(
        project_id=project_id,
        query=query,
        results=scored[: max(top_k, 1)],
    )
