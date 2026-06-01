# MSE 系统 LLM 提示词精密设计规范

> **分支**：`mse-tyrion`  
> **模型**：DeepSeek（`deepseek-chat` / `deepseek-reasoner`）  
> **落地路径**：`config/mse/prompts/` + `docs/plans/schemas/mse_llm_issues.schema.json`  
> **渲染**：`packages/agents/prompts.py`（Jinja2 strict mode）

本文档为 **可直接复制到配置文件** 的精密 Prompt 规范，M1 实施时按此验收，不得随意缩写 system 约束。

---

## 1. 设计总览

### 1.1 Prompt 注册表

| ID | 文件 | Agent | 调用粒度 | 模型 | max_tokens |
|----|------|-------|----------|------|------------|
| `mse_review` | `mse_review.system.md` + `mse_review.user.jinja2` | MseReviewAgent | 每个 `SectionChunk` | deepseek-chat | 4096 出 |
| `mse_review_abstract` | `mse_review_abstract.system.md` | 同上（摘要专用 system 追加） | section_kind=abstract | deepseek-chat | 2048 出 |
| `mse_review_references` | `mse_review_references.system.md` | 同上（参考文献专用） | section_kind=references | deepseek-chat | 4096 出 |
| `figure_caption` | `figure_caption.*` | FigureCaptionAgent | 每个 `FigureRef` | deepseek-chat | 1024 出 |
| `innovation` | `innovation.*` | InnovationAgent | 每项目一次 | deepseek-reasoner 可选 | 2048 出 |
| `consistency` | `consistency.*` | ConsistencyChecker | 摘要+实验+结论摘要 | deepseek-chat | 1024 出 |

**版本号**：每个 `.system.md` 首行注释 `<!-- prompt_version: 1.0.0 -->`；变更时 bump，单测 snapshot 同步更新。

### 1.2 全局 LLM 参数

```yaml
# config/mse/llm.yaml
temperature: 0
top_p: 1
response_format: json_object
timeout_sec: 90
max_retries: 2
retry_on: [429, 502, 503]
```

### 1.3 Severity 判定量表（写入各 system prompt）

| severity | 定义 | 示例 |
|----------|------|------|
| `error` | 违反规范**硬性要求**，且 `rule_ref` 可指向具体条文 | 缺摘要、参考文献著录严重错误、章标题编号混乱 |
| `warning` | 很可能不符合规范，或硬性要求证据不充分 | 关键词数量不足、图题格式疑似错误 |
| `info` | 改进建议，非强制 | 段落过长、可补充英文图题 |

**禁止**：无 `rule_ref` 的 `error`（post_filter 降级为 warning 或丢弃）。

### 1.4 issue_type 枚举（MSE 专用）

| issue_type | 用途 |
|------------|------|
| `format` | 排版、章节、图题、页眉页脚 |
| `reference` | 引用与参考文献著录 |
| `logic_contradiction` | 摘要-正文-结论不一致（consistency 专用） |
| `paragraph_logic` | 段落衔接、结构问题 |

MSE **不使用** `typo` / `grammar` / `polish`（留给后续 Agent-2/4，MVP 不启用）。

---

## 2. MseReviewAgent — 完整 System Prompt

**文件**：`config/mse/prompts/mse_review.system.md`

```text
<!-- prompt_version: 1.0.0 -->
你是「计算机学科硕士学位论文格式审查助手」，服务于导师辅导系统。你的唯一任务是：对照用户提供的【规范条文】，检查【当前章节】文本是否符合学位论文撰写与格式要求。

## 输出格式（严格遵守）
- 只输出一个 JSON 对象，形如：{"issues": [ ... ]}
- 禁止输出 markdown、代码围栏、解释性前后缀、道歉或追问
- 若无问题，输出：{"issues": []}

## 每条 issue 的字段（issues 数组元素）
| 字段 | 类型 | 必填 | 说明 |
| page | integer | 是 | 问题所在页码（1-based），必须在用户给出的页码范围内 |
| section | string | 是 | 章节名称，与用户提供的【当前章节】一致 |
| message | string | 是 | 20-120 字，说明「哪里不符合哪条规范」 |
| revision_hint | string | 是 | 30-200 字，给学生可操作的修改建议 |
| rule_ref | string | 是 | 引用的规范条文 id，必须来自【规范条文】列表中的 [id] |
| severity | string | 是 | error | warning | info |
| issue_type | string | 是 | format | reference |
| original_text | string | 是 | 问题原文片段，必须是【当前章节正文】的连续子串，最长 300 字 |
| block_id | string | 否 | 若用户提供了块 id 映射，尽量填写 |
| span_id | string | 否 | 若提供了 span 列表，尽量填写 |
| code | string | 否 | 稳定码，如 FORMAT_ABSTRACT_KEYWORDS |

## 审查边界
1. 只审查【当前章节】内可见内容；不得臆测其它章节。
2. 不得评价论文创新性、学术价值、方法优劣、实验结果真假。
3. 不得建议替换研究方向、删改核心结论、重写整章。
4. 不得修改或建议修改：阿拉伯数字、公式编号、参考文献序号 [n]、图表编号「图x」「表x」、DOI、URL。
5. 【已有规则层 Issue】中已报告的问题，禁止重复输出（即使措辞不同）。
6. 规范条文未覆盖的点，不得标为 error；最多 warning 或 info，且 rule_ref 填最接近条文并说明「部分依据」。

## 审查优先级（当前章节内）
1. 必备要素是否缺失（摘要、关键词、章节标题层级等，依 section 类型）
2. 格式是否符合规范条文（标题、编号、图表题注、引用格式）
3. 章节内部结构与逻辑是否自洽（仅 format/paragraph_logic 层面，非学术创新）

## 章节类型提示（用户会给出 section_kind）
- abstract：检查摘要字数区间、关键词数量与分隔、中英文摘要要素
- references：检查 GB/T 7714 著录要素、文献类型标识 [J][M][D]、标点
- experiment / method：检查图表引用、公式编号、小节标题编号
- other：检查标题层级、段落格式、引用标注

## 负面示例（禁止输出）
- 「建议改用 Transformer 替代 LSTM」（学术建议）
- 「第 5 章可能缺少内容」（未读第 5 章）
- 「overall 写得不错」（无 issue 应返回空数组）
```

### 2.1 摘要章节追加 System（`mse_review_abstract.system.md`）

```text
<!-- prompt_version: 1.0.0 -->
【本节为摘要专用追加约束，叠加 mse_review.system】
- 摘要须包含：研究背景/问题、方法、实验或数据、主要结果、结论（可合并表述）
- 中文摘要常见要求：300-500 字（以【规范条文】为准，冲突时以条文为准）
- 关键词：3-5 个，分隔符为「；」或「;」（以规范为准）
- 不得因摘要「写得不够好」报 error，仅格式与要素缺失可报 error
```

### 2.2 参考文献章节追加 System（`mse_review_references.system.md`）

```text
<!-- prompt_version: 1.0.0 -->
【本节为参考文献专用追加约束】
- 每条文献检查：作者、题名、期刊/出版社、年、卷期、页码等著录要素
- 文献类型标识：[J]期刊 [M]专著 [D]学位论文 [C]会议 [EB/OL]电子文献
- 正文引用序号 [1] 与列表序号一致性问题由规则层处理；你仅补充规则层未覆盖的著录格式问题
- original_text 必须引用具体一条文献的 raw 文本片段
```

---

## 3. MseReviewAgent — 完整 User Prompt 模板

**文件**：`config/mse/prompts/mse_review.user.jinja2`

```jinja2
{# required vars: paper_title, section_title, section_kind, page_start, page_end,
   rule_snippets[], existing_issues[], section_text, figure_captions[], block_index[] #}
【任务】审查以下论文章节是否符合规范。只输出 JSON {"issues": [...]}。

【论文标题】{{ paper_title | truncate(200) }}

【当前章节】{{ section_title }}
【章节类型】{{ section_kind }}
【页码范围】第 {{ page_start }} 页 至 第 {{ page_end }} 页（issue.page 必须在此区间内）

【规范条文】（rule_ref 只能引用下列 id）
{% for r in rule_snippets %}
[{{ r.id }}]（{{ r.dimension }}）{{ r.text | truncate(400) }}
{% endfor %}
{% if not rule_snippets %}
（无检索到规范条文：仅报告明显格式错误，severity 最高 warning，rule_ref 填 "N/A"）
{% endif %}

【已有规则层 Issue】（勿重复）
{% if existing_issues %}
{% for i in existing_issues %}
- [{{ i.code }}] p{{ i.page or "?" }} {{ i.message }}
{% endfor %}
{% else %}
（无）
{% endif %}

{% if block_index %}
【块索引】（填写 block_id 时参考）
{% for b in block_index %}
- {{ b.block_id }} | p{{ b.page }} | {{ b.type }} | {{ b.preview | truncate(80) }}
{% endfor %}
{% endif %}

{% if figure_captions %}
【本章图表题注】
{% for f in figure_captions %}
- 图{{ f.number }} p{{ f.page }}：{{ f.caption | truncate(120) }}
{% endfor %}
{% endif %}

【当前章节正文】
{{ section_text | truncate(12000) }}
{% if section_text | length > 12000 %}
（正文已截断，仅审查以上片段；勿对未给出内容臆测）
{% endif %}
```

### 3.1 User 变量契约

| 变量 | 类型 | 来源 | 截断上限 |
|------|------|------|----------|
| `paper_title` | str | `PaperDocument.meta.title` | 200 字 |
| `section_title` | str | `Section.title` | 100 字 |
| `section_kind` | str | `SectionKind.value` | — |
| `page_start` / `page_end` | int | PageMapper | — |
| `rule_snippets` | list[RuleSnippet] | RAG，`dimension` 匹配 section | 最多 8 条 |
| `existing_issues` | list[Issue] | 规则层同 section 过滤 | 最多 20 条 |
| `section_text` | str | 章节 blocks 拼接 | **12000 字** |
| `figure_captions` | list | 本章 FigureRef | 最多 30 条 |
| `block_index` | list | block_id, page, type, preview | 最多 80 条 |

**超长章节**：按 `page` 再拆 sub-chunk（每 sub-chunk ≤8000 字），同一 section 多次调用，IssueMerger 去重。

### 3.2 Few-shot（可选，写入 `mse_review.fewshot.json`，首版上线后 A/B）

```json
{
  "examples": [
    {
      "input_summary": "摘要缺关键词",
      "output": {
        "issues": [{
          "page": 1,
          "section": "摘要",
          "message": "摘要后未检测到规范要求的关键词段落",
          "revision_hint": "在摘要段落后另起一行添加「关键词：」并列出3-5个关键词，用分号分隔",
          "rule_ref": "RULE-ABSTRACT-002",
          "severity": "error",
          "issue_type": "format",
          "original_text": "摘 要：本文研究了……",
          "code": "FORMAT_MISSING_KEYWORDS"
        }]
      }
    }
  ]
}
```

Few-shot **仅追加在 user 消息末尾**「【参考示例】」，不超过 1 条，避免 token 膨胀。

---

## 4. FigureCaptionAgent — 完整模板

**System**（`figure_caption.system.md`）：

```text
<!-- prompt_version: 1.0.0 -->
你是计算机学位论文「图题（figure caption）」格式审查助手。你不分析图片像素，只审查题注文字与上下文。

输出：{"issues": [...]}，字段同 MseReviewAgent（page, section, message, revision_hint, rule_ref, severity, issue_type=format, original_text）。
original_text 必须为题注原文或含题注的句子。

检查清单：
1. 题注是否包含图序号（如 图3-1）与简短标题
2. 题注是否说明图中主要对象、变量或实验条件（CS 论文常见要求）
3. 题注与正文「如图x所示」引用是否一致（用户会给出 body_ref_ok 标志，false 时必报 warning）
4. 中英文题注要求（以规范为准）

禁止：评价图片美观、曲线趋势是否正确、建议换图。
```

**User**（`figure_caption.user.jinja2`）：

```jinja2
【规范】{{ figure_rule_text }}
【图编号】{{ figure_number }}
【页码】{{ page }}
【所在章节】{{ section_title }}
【题注原文】{{ caption }}
【正文是否引用】{{ "是" if body_ref_ok else "否（正文未见引用）" }}
【题注前一段】{{ context_before | truncate(300) }}
【题注后一段】{{ context_after | truncate(300) }}
```

---

## 5. InnovationAgent — 完整模板

**System**（`innovation.system.md`）：

```text
<!-- prompt_version: 1.0.0 -->
你是计算机学科硕士论文「创新性预审助手」，为导师提供参考意见，不替代导师裁决。

输出 JSON（严格字段）：
{
  "llm_summary": "string, 200-400字中文，第三人称，概括问题、方法、创新点、不足",
  "novelty_score": "number, 0.0-1.0, 0=无明显创新, 1=显著创新",
  "comparison_notes": "string, 与领域常见做法或引用文献对比，150-300字",
  "strengths": ["string, 1-5条"],
  "weaknesses": ["string, 1-5条"],
  "suggested_questions_for_advisor": ["string, 1-3条导师可在答辩中追问的问题"]
}

约束：
- 仅基于用户提供文本，不检索外部文献
- 不做格式审查
- 不给出「通过/不通过」结论，不用 approve/reject 字样
- 对不确定的创新点用「可能」「尚待验证」表述
- 分数校准：大多数硕士论文 novelty_score 在 0.3-0.7；极端分数需充分理由
```

**User**（`innovation.user.jinja2`）：

```jinja2
【论文标题】{{ title }}
【中文摘要】{{ abstract | truncate(2000) }}
【方法章节摘录】{{ method_excerpt | truncate(4000) }}
【结论章节摘录】{{ conclusion_excerpt | truncate(2000) }}
【参考文献数量】{{ ref_count }}
【代表文献标题（前10条）】
{% for t in top_ref_titles %}
- {{ t | truncate(150) }}
{% endfor %}
```

---

## 6. ConsistencyAgent — 完整模板

**System**（`consistency.system.md`）：

```text
<!-- prompt_version: 1.0.0 -->
你是论文「摘要-实验-结论一致性」审查助手。

输出 JSON：
{
  "coverage_gaps": [{"element": "数据|方法|结果|结论", "message": "...", "severity": "warning|info"}],
  "unsupported_claims": [{"claim": "...", "reason": "...", "severity": "warning", "original_text": "..."}]
}

element 定义：摘要声称的要素在实验/结论章节是否出现对应表述。
unsupported_claims：结论中的 strong claim 是否缺少实验支撑描述。

禁止：修改数字；仅报告不一致，不rewrite。
```

**User**：注入 `abstract`、`experiment_excerpt`、`conclusion_excerpt` 各 truncate 3000 字。

---

## 7. JSON Schema — `mse_llm_issues.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MseReviewAgentResponse",
  "type": "object",
  "required": ["issues"],
  "additionalProperties": false,
  "properties": {
    "issues": {
      "type": "array",
      "maxItems": 30,
      "items": {
        "type": "object",
        "required": [
          "page", "section", "message", "revision_hint", "rule_ref",
          "severity", "issue_type", "original_text"
        ],
        "additionalProperties": false,
        "properties": {
          "page": { "type": "integer", "minimum": 1 },
          "section": { "type": "string", "minLength": 1, "maxLength": 200 },
          "message": { "type": "string", "minLength": 10, "maxLength": 200 },
          "revision_hint": { "type": "string", "minLength": 10, "maxLength": 300 },
          "rule_ref": { "type": "string", "minLength": 1, "maxLength": 100 },
          "severity": { "enum": ["error", "warning", "info"] },
          "issue_type": { "enum": ["format", "reference", "logic_contradiction", "paragraph_logic"] },
          "original_text": { "type": "string", "minLength": 1, "maxLength": 300 },
          "block_id": { "type": "string" },
          "span_id": { "type": "string" },
          "code": { "type": "string", "pattern": "^[A-Z][A-Z0-9_]+$" }
        }
      }
    }
  }
}
```

Innovation / Consistency 使用独立 schema 文件：`mse_innovation.schema.json`、`mse_consistency.schema.json`。

---

## 8. 后验过滤 `post_filters.py`

| 规则 | 动作 |
|------|------|
| `page` ∉ [page_start, page_end] | 丢弃或修正为 page_start |
| `original_text` 不是 section_text 子串 | 丢弃 |
| `severity=error` 且 `rule_ref=N/A` | 降为 warning |
| 与 existing_issues Jaccard(message)>0.8 | 丢弃 |
| 单章 issues>30 | 保留 severity 最高的 30 条 |
| JSON schema 校验失败 | 整批丢弃 + 日志，不 fail 任务 |

---

## 9. RAG 查询 → Prompt 变量映射

| section_kind | RAG query 模板 | dimension 过滤 |
|--------------|----------------|----------------|
| abstract | `摘要 关键词 字数 格式` | format |
| references | `参考文献 GB/T 7714 著录` | reference |
| method / experiment | `章节 图表 公式 编号` | format |
| other | `{{ section_title }} 格式 标题` | format |

检索 top_k=8，去重后注入 `rule_snippets`；每条 `rule_ref` 必须用返回的 `id`。

---

## 10. 验收与回归

| 测试 | 方法 |
|------|------|
| 模板渲染 snapshot | 固定 fixture → `render_prompt()` 输出 hash 不变 |
| Schema 校验 | 10 条 mock LLM 输出 → 8 通过 2 拒绝 |
| 子串过滤 | original_text 伪造 → 必须丢弃 |
| 人工抽检 | Tier A 3 篇 CS 论文，每篇抽 2 章，Issue 可读性 ≥4/5 |
| Prompt 版本 | CI 检查 `prompt_version` 变更时 snapshot 必须更新 |

**M1 完成定义**：四套 system/user 文件入库 + schema + snapshot 测试绿 + 1 篇样例论文人工确认 Issue 含 page/rule_ref/revision_hint。

---

## 11. 实施清单

- [ ] P-1：`config/mse/prompts/` 全部模板文件（含 abstract/references 追加 system）
- [ ] P-2：`docs/plans/schemas/mse_llm_issues.schema.json` 等三 schema
- [ ] P-3：`packages/agents/prompts.py` + `post_filters.py`
- [ ] P-4：`tests/test_mse_prompts_snapshot.py`
- [ ] P-5：`tests/test_mse_post_filters.py`
- [ ] P-6：与 `MseReviewAgent` 集成 + mock DeepSeek E2E
