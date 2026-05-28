# 后端 API 实施计划

> **当前实施范围**：本文档为仓库内**优先交付**的后端工作项。  
> 关联文档：[Agent 流水线计划](./agent-pipeline.md) · [模型微调计划](./model-finetuning.md)

## 目标

对齐飞书《论文纠错 Agent 前端技术方案》与 PRD 的后端契约，在现有 `fudan-pager-check` 预检查 MVP 上扩展：

- 统一 API 响应与错误码
- 规范库、检测、结果、进度、决策、导出全链路
- Issue / Span 数据模型（供 Agent 与任意前端消费）

**不在范围**：前端 UI（`apps/web-next` 保持现状，仅作联调参考）。

## 需求来源

| 来源 | 链接/路径 |
|------|-----------|
| 飞书技术方案 | [论文纠错 Agent 前端技术方案](https://ycn0g9jly13e.feishu.cn/wiki/QZBdwEwUiiRteck0WhLcjEs8nBe) |
| 产品 PRD | [`论文纠错智能Agent产品需求文档.docx`](../../论文纠错智能Agent产品需求文档.docx) |

## 现状基线

```mermaid
flowchart LR
  Upload["POST /v1/papers"] --> Worker["apps/worker/tasks.py"]
  Worker --> Parser["DualSourceFusionParser"]
  Parser --> Orchestrator["CheckOrchestrator"]
  Orchestrator --> Rules["4 rule checkers"]
  Rules --> Report["CheckReport JSON"]
```

**已有**

| 能力 | 位置 |
|------|------|
| JWT 认证 | `apps/api/auth_routes.py` |
| 上传 + 异步检测 | `apps/api/routes/papers.py` |
| 四类规则检查 | `packages/checks/` |
| 任务/报告存储 | `packages/storage/jobs.py` |
| 文档模型 Section/Block | `packages/schema/models.py` |

**缺失**

- `rule_bases` API、统一响应壳
- `POST /v1/check`、`GET /v1/result/*` 语义
- Issue 扩展字段（`span_id`、`original_text`、`suggested_text`、`issue_type`）
- Span 模型与 `span_builder`
- SSE 细粒度进度、任务 FSM
- 决策持久化、预览合成、Word/PDF 导出

---

## Phase 1 — 契约与数据模型（P0）

**验收**：第三方可 `GET rule_bases` → `POST check` → 轮询 `GET tasks/{id}` → `GET result/{id}` 拿到结构化 Issue + Document。

### 1.1 统一响应与错误码

**新增** `packages/schema/api_response.py` + FastAPI 异常处理器。

```python
# 成功
{ "code": 0, "message": "ok", "data": { ... } }
# 失败
{ "code": "DETECT_FAILED", "message": "...", "detail": "..." }
```

**错误码**：`DETECT_FAILED` | `FILE_TOO_LARGE` | `UNSUPPORTED_FORMAT` | `TASK_NOT_FOUND` | `TASK_NOT_READY` | `RULE_BASE_NOT_FOUND`

### 1.2 规范库 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/rule_bases` | 规范列表 |
| GET | `/v1/rule_bases/{id}` | 详情 + 按维度分组的 `summary` |

**实现**

- 读取 `config/journals/*.yaml`，扩展 `summary` 字段（或离线生成写入 YAML）
- 路由：`apps/api/routes/rule_bases.py`
- GB/T 7714 规则包后续以独立 YAML/MD 纳入同一加载器

### 1.3 检测提交

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/check` | 上传 + `rule_base_id` → `{ task_id, status }` |

- 与 `POST /v1/papers` **并存**，共用 enqueue（`apps/worker/tasks.py`）
- 表单：`file`（`.pdf` / `.docx`），`rule_base_id`（默认 `generic`）
- 上限 50MB；分片见 Phase 3

**路由** `apps/api/routes/check.py`

### 1.4 结果 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/result/{task_id}` | 完整检测报告（Issue 列表 + summary + parse_quality） |
| GET | `/v1/result/{task_id}/document` | Section + Span 树 |

**模型扩展**（`packages/schema/models.py`）

```python
class IssueType(str, Enum):
    FORMAT = "format"
    TYPO = "typo"
    GRAMMAR = "grammar"
    POLISH = "polish"
    LOGIC_CONTRADICTION = "logic_contradiction"
    PARAGRAPH_LOGIC = "paragraph_logic"
    SENTENCE_SPLIT = "sentence_split"
    REFERENCE = "reference"

class Span(BaseModel):
    id: str
    section_id: str
    start_offset: int
    end_offset: int
    text: str

class Issue(BaseModel):
    id: str
    issue_type: IssueType
    original_text: str = ""
    suggested_text: str = ""
    span_id: str | None = None
    code: str
    severity: IssueSeverity
    message: str
    suggestion: str = ""
    evidence: str = ""
    section: str | None = None
    line: int | None = None
```

**新增** `packages/parser/span_builder.py`：Block → 句子级 Span。

**JobRecord 扩展**：持久化 `document: PaperDocument + spans`（检测完成后写入）。

**路由** `apps/api/routes/result.py`

### 1.5 任务状态

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/v1/tasks/{task_id}` | `status`, `current_stage`, `progress_percent`, `progress_message` |

### Phase 1 任务清单

- [x] `api_response.py` + 全局异常处理
- [x] `rule_bases` 路由 + YAML `summary` 扩展
- [x] `check` 路由，复用 worker enqueue
- [x] `IssueType` / `Span` / `Issue.id` 模型迁移（兼容旧 report）
- [x] `span_builder` + worker 写入 document/spans
- [x] `result` / `tasks` 路由
- [x] 测试：`tests/test_check_api.py`（上传 → 完成 → result 结构断言）

---

## Phase 2 — SSE 进度与 FSM（P1）

**验收**：`GET /v1/detect/progress/{task_id}` 推送 stage 事件；检测中 `POST /v1/check` 同 task 被拒绝。

### 2.1 SSE

| 方法 | 路径 |
|------|------|
| GET | `/v1/detect/progress/{task_id}` |

```
event: progress
data: {"stage":"FORMAT_CHECK","percent":35,"message":"正在检测行间距..."}

event: done
data: {"stage":"DONE","percent":100,"message":"检测完成，共发现 17 项问题"}
```

**stage 枚举**：`UPLOADING` → `PARSING` → `FORMAT_CHECK` → `TYPO_CHECK` → `GRAMMAR_CHECK` → `POLISH` → `LOGIC_CHECK` → `REFERENCE_CHECK` → `DONE` | `ERROR`

**实现**

- `packages/orchestrator/progress.py`：Redis Pub/Sub（无 Redis 时进程内 Queue）
- `apps/api/routes/progress.py`：`StreamingResponse`
- Worker / [Agent 编排](./agent-pipeline.md) 各 stage 前后 `publish()`

### 2.2 任务 FSM

**新增** `packages/orchestrator/fsm.py`

```
IDLE → UPLOADING → DETECTING → DONE
         ↓              ↓
        ERROR ← RETRYING
```

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/tasks/{task_id}/restart` | 换 `rule_base_id` 重新检测 |

### Phase 2 任务清单

- [ ] `progress.py` + SSE 路由
- [ ] `JobRecord` 增加 stage/percent/message
- [ ] `fsm.py` + 非法状态拦截
- [ ] Worker 接入 progress（先对现有 4 checker 映射 stage，Agent 接入后扩展）
- [ ] 测试：SSE 事件序列、FSM 非法转换

---

## Phase 3 — 决策、预览、导出（P1–P2）

**验收**：决策落库 → `GET preview` 反映 accept/custom → `POST export` 产出 docx/pdf。

### 3.1 决策 API

| 方法 | 路径 |
|------|------|
| GET | `/v1/tasks/{task_id}/decisions` |
| PUT | `/v1/tasks/{task_id}/decisions` |
| PATCH | `/v1/tasks/{task_id}/decisions/{issue_id}` |

```python
class DecisionAction(str, Enum):
    PENDING = "pending"
    ACCEPT = "accept"
    REJECT = "reject"
    CUSTOM = "custom"

class Decision(BaseModel):
    issue_id: str
    action: DecisionAction
    custom_content: str | None = None
    updated_at: str
```

**存储** `packages/storage/decisions.py`  
**路由** `apps/api/routes/decisions.py`

### 3.2 预览合成

| 方法 | 路径 |
|------|------|
| GET | `/v1/tasks/{task_id}/preview` |

**逻辑** `packages/orchestrator/preview.py`：按 decisions 合并 span 文本，返回高亮元数据 `{ span_id, highlight: "accepted"|"custom" }`。

### 3.3 导出

| 方法 | 路径 |
|------|------|
| POST | `/v1/tasks/{task_id}/export` |
| GET | `/v1/tasks/{task_id}/export/{format}` |

Body 示例：`{ "format": "docx"|"pdf", "decisions": [...] }`  
响应含 `unresolved_count`（未处理 Issue 数）。

**路由** `apps/api/routes/export.py`

### 3.4 分片上传（P2，可选）

| 方法 | 路径 |
|------|------|
| POST | `/v1/upload/init` |
| POST | `/v1/upload/chunk` |
| POST | `/v1/upload/complete` |

### Phase 3 任务清单

- [ ] decisions 存储 + CRUD 路由
- [ ] preview 合成 + 路由
- [ ] docx 导出（python-docx / pandoc）
- [ ] pdf 导出（docx → LibreOffice / weasyprint）
- [ ] 分片上传（可选）
- [ ] 测试：决策 → preview 一致性 → 导出文件非空

---

## RAG-1：规范知识库（后端侧，支撑 rule_bases）

> Agent 消费细节见 [agent-pipeline.md](./agent-pipeline.md)。后端 Phase 1 至少需要 **静态 summary**；RAG-1 为增强项。

| 项 | 说明 |
|----|------|
| 目录 | `packages/rag/rule_index.py`, `rule_retriever.py` |
| 输入 | `config/journals/*.yaml` + GB/T 7714 文档 |
| 输出 | 向量索引；`retrieve_rules(rule_base_id, query, top_k)` |
| CLI | `python -m rag.index_rules --rule-base scut_natural_science` |

**与 API 关系**：`GET /v1/rule_bases/{id}` 的 `summary` 可来自 RAG 聚合或预计算缓存。

---

## 与 Agent / 微调 的集成点

后端完成 Phase 1 后，[Agent 流水线](./agent-pipeline.md) 通过以下扩展接入，**无需改对外 API**：

| 集成点 | 说明 |
|--------|------|
| `AGENT_MODE` | `rules` \| `agents` \| `hybrid`（env） |
| `agent_runner.py` | 替换/并联 `CheckOrchestrator` |
| `progress.publish` | 各 DetectStage 上报 SSE |
| `ModelRouter` | [微调计划](./model-finetuning.md) FT-6 注入 LLM 调用 |

当前 Phase 1–2 可用现有 4 checker 填充 stage，保证 SSE/result 链路先通。

---

## 目录结构（新增）

```
apps/api/routes/
├── check.py
├── result.py
├── rule_bases.py
├── progress.py
├── decisions.py
└── export.py
packages/
├── schema/api_response.py
├── parser/span_builder.py
├── orchestrator/fsm.py
├── orchestrator/preview.py
├── orchestrator/progress.py
├── storage/decisions.py
└── rag/                    # RAG-1
    ├── rule_index.py
    └── rule_retriever.py
```

---

## 飞书接口对照

| 飞书 | 后端路径 |
|------|----------|
| `GET /api/rule_bases` | `GET /v1/rule_bases` |
| `POST /api/check` | `POST /v1/check` |
| `GET /api/result/{task_id}` | `GET /v1/result/{task_id}` |
| SSE progress | `GET /v1/detect/progress/{task_id}` |
| 决策 + 导出 | `PUT .../decisions` + `POST .../export` |

网关可将 `/api` 别名到 `/v1`。

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 旧客户端依赖 `/v1/papers` | 保留并存，文档标注 deprecate 时间表 |
| Issue 模型破坏性变更 | 迁移层：旧 report 读取时补 `id`/`issue_type` 默认值 |
| SSE 生产环境 | Redis Pub/Sub；开发环境 in-memory |
| docx 排版复杂 | Phase 3 先保证文本正确，样式迭代 |

---

## 推荐实施顺序

1. Phase 1（模型 + rule_bases + check + result + tasks）
2. Phase 2（SSE + FSM）
3. RAG-1（可与 Phase 1 并行）
4. [Agent 流水线](./agent-pipeline.md) 接入 worker
5. Phase 3（decisions + preview + export）
6. [模型微调](./model-finetuning.md) 经 ModelRouter 可选上线
