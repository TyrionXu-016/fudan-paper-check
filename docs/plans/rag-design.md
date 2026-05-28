# RAG 设计计划（RAG-1 / RAG-2）

> **读者**：负责规范检索、文档上下文、Agent Prompt 注入的后端/算法工程师。  
> **依赖**：[backend-api.md](./backend-api.md) Phase 1 已完成；[agent-pipeline.md](./agent-pipeline.md) 消费本设计。  
> **状态**：RAG-1 MVP 已落地；RAG-1 增强与 RAG-2 待实施。

---

## 0. 设计原则：规范检查用规则切片，不用「全文语义 RAG」

论文**规范检查**（格式、结构、参考文献）本质是 **可判定规则**，不是开放式问答。因此：

| 层次 | 做法 | 职责 |
|------|------|------|
| **规则引擎** | `packages/checks/` + YAML `patterns` | **检测**：是否违规，产出 Issue |
| **RAG-1 规则切片** | YAML/MD → `RuleChunk` → BM25 检索 | **引用**：哪条规范、evidence、LLM/前端依据 |
| **向量 RAG（P2 可选）** | 仅在条文很多、关键词召回不足时 | 增强 retrieve，**不替代** checker |

**RAG-1 切片粒度**：一条规则 / 一个 YAML 字段 / 一个 Markdown 小节 — **不是** 512 token 滑动窗口，也**不是**整本 PDF OCR 后语义切块。

**RAG-2** 则不同：切的是**当前论文** Span 上下文，供错别字/逻辑/润色 Agent 使用，与规范库无关。

---

## 1. 目标与边界

| 系统 | 检索对象 | 消费者 | 生命周期 |
|------|----------|--------|----------|
| **RAG-1** | 期刊规范 YAML、GB/T 7714、后续规则 MD | Agent-1、规则 checker、API `/retrieve` | 按 `rule_base_id` 持久化索引 |
| **RAG-2** | 当前论文 `PaperDocument` + `Span` | Agent-2/3/4 LLM Prompt | 按 `task_id` 临时索引，任务结束 TTL 清理 |

**不在范围**：前端检索 UI；跨论文知识库；微调数据集构建（见 [model-finetuning.md](./model-finetuning.md)）。

---

## 2. 架构

```mermaid
flowchart LR
  subgraph RAG1 [RAG-1 规范库]
    YAML[config/journals/*.yaml]
    GBT[config/rules/gbt7714.md]
    IDX1[data/rag/{rule_base_id}.json]
    YAML --> Index1[rule_index.build_index]
    GBT --> Index1
    Index1 --> IDX1
    IDX1 --> Ret1[retrieve_rules]
  end

  subgraph RAG2 [RAG-2 文档上下文]
    Doc[PaperDocument + Spans]
    IDX2[data/rag/tasks/{task_id}.json]
    Doc --> Index2[doc_index.build_task_index]
    Index2 --> IDX2
    IDX2 --> Ret2[retrieve_context]
  end

  Ret1 --> A1[Agent-1 格式/引用]
  Ret2 --> A2[Agent-2 纠错]
  Ret2 --> A3[Agent-3 逻辑]
  Ret2 --> A4[Agent-4 润色]
```

---

## 3. RAG-1 — 规范知识库

### 3.1 已实现（基线）

| 项 | 位置 |
|----|------|
| 索引构建 | `packages/rag/rule_index.py` |
| 检索 | `packages/rag/rule_retriever.py` → `retrieve_rules(rule_base_id, query, top_k)` |
| CLI | `python -m rag.index_rules --rule-base generic` / `--all` |
| API | `GET /v1/rule_bases/{id}/retrieve?q=&top_k=` |
| 索引产物 | `data/rag/{rule_base_id}.json` |
| 国标摘要 | `config/rules/gbt7714.md` |

**Chunk 来源**（每个 `rule_base_id`）：

- YAML `summary.*`（format / reference / typo / …）
- `required_sections` / `optional_sections`
- `patterns.*` / `warnings.*`
- GB/T 7714 各 Markdown 小节（dimension=`reference`）

**检索算法（MVP）**：中文 bigram token + BM25 + 子串匹配 fallback。

### 3.2 RAG-1 增强任务（可分配）

| ID | 任务 | 优先级 | 验收标准 | 建议负责人 |
|----|------|--------|----------|------------|
| R1-1 | 扩展 `config/rules/`：各校学报细则 MD（华南理工等） | P1 | 索引 chunk 数增加；retrieve「表题格式」命中学报条文 | 规则工程 |
| R1-2 | `retrieve_rules(..., dimensions=[...])` 过滤 dimension | P1 | Agent-1 只拉 format+reference | 后端 |
| R1-3 | 向量检索升级（可选 pgvector / Chroma） | P2 | 同 query 召回率 ≥ MVP；延迟 < 200ms | 算法 |
| R1-4 | 索引 manifest：`built_at`, `source_hashes`, `chunk_count` | P2 | CLI 输出版本；API 可返回 index 元信息 | 后端 |
| R1-5 | 部署：镜像 build 时预跑 `rag.index_rules --all` | P1 | 冷启动无需首次检索建索引 | DevOps |
| R1-6 | 测试集 `tests/fixtures/rag_queries.json` + 回归 | P1 | CI 断言 top-1 命中预期 source | QA/后端 |

### 3.3 RAG-1 内部 API 契约

```python
# packages/rag/rule_retriever.py（现有 + 扩展）

def retrieve_rules(
    rule_base_id: str,
    query: str,
    top_k: int = 5,
    dimensions: list[str] | None = None,  # R1-2 待加
) -> RetrieveRulesResponse: ...

# Agent 侧封装（待建 packages/rag/rule_retriever.py 或 agents 内）
class RuleRetriever:
    def retrieve(self, query: str, *, dimensions: list[str] | None = None) -> list[RuleSnippet]:
        ...
```

**Prompt 注入格式**（Agent-1 / ReferenceChecker 统一）：

```text
【适用规范摘录】
1. [format] 摘要、关键词、章节结构…（来源：generic.yaml#summary.format）
2. [reference] 顺序编码制：按引用先后用阿拉伯数字…（来源：gbt7714.md#正文引用）
```

### 3.4 数据文件规范

```
config/
├── journals/
│   ├── generic.yaml
│   └── scut_natural_science.yaml
└── rules/
    ├── gbt7714.md              # 已有
    └── journals/               # R1-1 建议目录
        └── scut_natural_science.md
data/rag/
├── generic.json
├── scut_natural_science.json
└── tasks/                      # RAG-2，见下节
    └── {task_id}.json
```

---

## 4. RAG-2 — 文档上下文检索

### 4.1 设计目标

为 LLM Agent 提供 **span 级** 上下文，避免整篇论文塞入 Prompt：

- 待检 span 前后窗口
- 同 section 其他关键 span（标题、图表 caption）
- 摘要 / 结论片段（供逻辑 Agent 对照）
- 可选：与待检 span 共享数字、缩写、引用标记的 span

### 4.2 模块设计

**新增文件**：

```
packages/rag/
├── doc_index.py       # build_task_index, drop_task_index
├── doc_retriever.py   # retrieve_context, retrieve_section_summary
└── task_store.py      # TTL 清理（可选 cron / worker 结束时）
```

**索引 JSON Schema**（`data/rag/tasks/{task_id}.json`）：

```json
{
  "task_id": "uuid",
  "paper_title": "…",
  "built_at": "ISO8601",
  "spans": [
    {
      "id": "span-001",
      "section_id": "sec-abstract",
      "section_kind": "abstract",
      "text": "…",
      "line_start": 12,
      "line_end": 12,
      "neighbors": ["span-000", "span-002"],
      "tags": ["numeric", "citation"]
    }
  ],
  "sections": [
    { "id": "sec-abstract", "kind": "abstract", "title": "摘要", "span_ids": ["…"] }
  ],
  "captions": [
    { "kind": "figure", "number": 1, "text": "图1 …", "span_id": "…" }
  ]
}
```

### 4.3 内部 API

```python
def build_task_index(
    task_id: str,
    doc: PaperDocument,
    spans: list[Span],
) -> Path:
    """解析完成后、Agent 运行前调用一次。"""

def retrieve_context(
    task_id: str,
    span_id: str,
    *,
    window: int = 2,
    top_k: int = 8,
    include_section_summary: bool = True,
) -> list[ContextSnippet]:
    """
    返回按相关度排序的文本片段。
    ContextSnippet: { span_id, text, role: "target"|"before"|"after"|"section"|"caption", score }
    """

def drop_task_index(task_id: str) -> None:
    """任务 DONE/FAILED 后调用；默认 TTL 24h。"""
```

**检索策略（MVP，无向量）**：

1. 必选：目标 span + 索引中 `neighbors`（±window）
2. 同 `section_id` 首尾 span（段落主旨）
3. 若 span 含 `[数字]` 引用，召回 references section 前 3 条
4. 若含 `%` / `pcu` 等，召回 abstract + conclusion 中含同数字的 span（供 Agent-3）
5. 打分：距离越近越高；跨 section 降权

**Phase 2 升级（R2-4）**：span embedding 批量编码，cosine 召回 top_k。

### 4.4 RAG-2 任务清单

| ID | 任务 | 优先级 | 验收标准 | 依赖 |
|----|------|--------|----------|------|
| R2-1 | `doc_index.py`：建索引 + neighbors 图 | P0 | 单测：10 span 论文 neighbors 正确 | SpanBuilder |
| R2-2 | `doc_retriever.py`：retrieve_context MVP | P0 | 单测：给定 span_id 返回 ≥3 条上下文 | R2-1 |
| R2-3 | Worker 接入：`build_task_index` 在 parse 后、check 前 | P0 | E2E 索引文件落盘 | R2-1 |
| R2-4 | `drop_task_index` + 24h TTL | P1 | 磁盘无泄漏 | R2-3 |
| R2-5 | Agent-2 Prompt 注入 `retrieve_context` | P0 | 集成测试 mock LLM 收到 context | Agent-2 |
| R2-6 | Agent-3 摘要/结论 cross-section 召回 | P1 | 逻辑 fixture 含 abstract 数字 | R2-2 |
| R2-7 | 向量索引 PoC（可选） | P2 | 万字论文 recall@5 提升文档 | R2-2 |
| R2-8 | `tests/test_doc_retriever.py` + fixture | P0 | CI 通过 | R2-2 |

### 4.5 与 Worker 集成点

```python
# apps/worker/tasks.py — process_paper_job（示意）

doc = parser.parse_files(...)
spans = build_spans(doc)
build_task_index(job_id, doc, spans)   # R2-3

try:
    if agent_mode in ("agents", "hybrid"):
        report = agent_runner.run(doc, spans, ...)
    else:
        report = CheckOrchestrator(...).run(doc, job_id, on_progress=...)
finally:
    drop_task_index(job_id)  # R2-4，或异步 TTL
```

---

## 5. 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `RAG_INDEX_DIR` | `data/rag` | RAG-1 索引根目录 |
| `RAG_TASK_TTL_HOURS` | `24` | RAG-2 任务索引保留时间 |
| `RAG_DOC_WINDOW` | `2` | 上下文 neighbor 窗口 |
| `RAG_USE_EMBEDDINGS` | `false` | 是否启用向量检索 |

---

## 6. 测试与验收

### 6.1 RAG-1 回归用例（建议 `tests/fixtures/rag_queries.json`）

| query | rule_base_id | 期望 top-1 source 含 |
|-------|--------------|----------------------|
| 参考文献 顺序编码 | generic | `gbt7714` 或 `reference` |
| 摘要 关键词 | scut_natural_science | `summary.format` |
| 表题 图题 | scut_natural_science | `patterns.table_caption` |

### 6.2 RAG-2 回归用例

- Fixture：`tests/fixtures/sample_paper_spans.json`（从 `samples/*_maker.md` 导出）
- 断言：`retrieve_context(task_id, "span-with-number-in-abstract")` 包含 conclusion 中同数字 span

### 6.3 性能基线

| 操作 | 目标 |
|------|------|
| RAG-1 retrieve | < 50ms（JSON 索引，top_k=5） |
| RAG-2 build_task_index | < 500ms（1 万字，纯规则） |
| RAG-2 retrieve_context | < 20ms |

---

## 7. 实施顺序

```
RAG-1 基线（已完成）
    → R1-1 / R1-2 / R1-5 / R1-6（规范扩展 + 过滤 + 部署）
    → R2-1 → R2-2 → R2-3 → R2-8（RAG-2 MVP）
    → R2-5 / R2-6（Agent 消费）
    → R1-3 / R2-7（向量升级，可选）
```

**与 Agent 并行**：R2-1/2/3 可与 Agent-1 并行；Agent-2 依赖 R2-5。

---

## 8. 相关文档

- [agent-implementation-guide.md](./agent-implementation-guide.md) — Agent 如何使用 RAG
- [agent-pipeline.md](./agent-pipeline.md) — Agent 总览
- [backend-api.md](./backend-api.md) — 对外 API（RAG-1 retrieve 已暴露）
