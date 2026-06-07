from __future__ import annotations

import math
import re
from collections import Counter

from pydantic import BaseModel, Field

from rag.rule_index import load_index


class RuleSnippet(BaseModel):
    id: str
    dimension: str
    text: str
    score: float
    source: str


class RetrieveRulesResponse(BaseModel):
    rule_base_id: str
    query: str
    results: list[RuleSnippet] = Field(default_factory=list)


_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for part in _TOKEN_RE.findall(text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", part):
            if len(part) <= 2:
                tokens.append(part)
            else:
                tokens.extend(part[i : i + 2] for i in range(len(part) - 1))
                tokens.append(part)
        elif part:
            tokens.append(part)
    return tokens


def _substring_score(query: str, text: str) -> float:
    score = 0.0
    lowered = text.lower()
    for term in _TOKEN_RE.findall(query.lower()):
        if len(term) < 2:
            continue
        if term in lowered:
            score += float(len(term))
    return score


def _bm25_score(query_tokens: list[str], doc_tokens: list[str], avg_dl: float, df: Counter, n_docs: int) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    k1 = 1.2
    b = 0.75
    dl = len(doc_tokens)
    tf = Counter(doc_tokens)
    score = 0.0
    for term in set(query_tokens):
        if term not in tf:
            continue
        doc_freq = df.get(term, 0)
        idf = math.log(1 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
        freq = tf[term]
        denom = freq + k1 * (1 - b + b * dl / max(avg_dl, 1))
        score += idf * (freq * (k1 + 1)) / max(denom, 1e-9)
    return score


def retrieve_rules(
    rule_base_id: str,
    query: str,
    top_k: int = 5,
    dimensions: list[str] | None = None,
) -> RetrieveRulesResponse:
    index = load_index(rule_base_id)
    if index is None:
        return RetrieveRulesResponse(rule_base_id=rule_base_id, query=query, results=[])

    chunks = index.get("chunks") or []
    if dimensions:
        chunks = [c for c in chunks if c.get("dimension") in dimensions]

    query_tokens = _tokenize(query)
    if not query_tokens:
        return RetrieveRulesResponse(rule_base_id=rule_base_id, query=query, results=[])

    tokenized_docs = [_tokenize(chunk.get("text", "")) for chunk in chunks]
    n_docs = max(len(tokenized_docs), 1)
    avg_dl = sum(len(doc) for doc in tokenized_docs) / n_docs if tokenized_docs else 1.0
    df: Counter = Counter()
    for doc in tokenized_docs:
        df.update(set(doc))

    scored: list[RuleSnippet] = []
    for chunk, doc_tokens in zip(chunks, tokenized_docs):
        text = chunk.get("text", "")
        score = _bm25_score(query_tokens, doc_tokens, avg_dl, df, n_docs)
        score = max(score, _substring_score(query, text))
        if score <= 0:
            continue
        scored.append(
            RuleSnippet(
                id=chunk["id"],
                dimension=chunk.get("dimension", ""),
                text=chunk.get("text", ""),
                score=round(score, 4),
                source=chunk.get("source", ""),
            )
        )

    scored.sort(key=lambda item: item.score, reverse=True)
    if not scored:
        for chunk, doc_tokens in zip(chunks, tokenized_docs):
            overlap = len(set(query_tokens) & set(doc_tokens))
            if overlap <= 0:
                continue
            scored.append(
                RuleSnippet(
                    id=chunk["id"],
                    dimension=chunk.get("dimension", ""),
                    text=chunk.get("text", ""),
                    score=float(overlap),
                    source=chunk.get("source", ""),
                )
            )
        scored.sort(key=lambda item: item.score, reverse=True)

    return RetrieveRulesResponse(
        rule_base_id=rule_base_id,
        query=query,
        results=scored[: max(top_k, 1)],
    )
