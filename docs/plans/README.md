# 实施计划索引

本目录存放论文纠错 Agent 后端及相关能力的分模块计划。

| 文档 | 范围 | 实施优先级 |
|------|------|------------|
| [backend-api.md](./backend-api.md) | 后端 API、数据模型、SSE、决策、导出、RAG-1 MVP | **P0 — 已完成** |
| [rag-design.md](./rag-design.md) | RAG-1 增强 + RAG-2 详细设计、任务 ID、验收 | **P1 — 待实施** |
| [agent-implementation-guide.md](./agent-implementation-guide.md) | Agent 可分工交付指南、Prompt/Schema、集成点 | **P1 — 待实施** |
| [agent-pipeline.md](./agent-pipeline.md) | Agent-1～5 架构总览、PRD 映射 | P1 — 参考总览 |
| [model-finetuning.md](./model-finetuning.md) | SFT/LoRA FT-0～FT-7、ModelRouter | 与 Agent 并行 |
| [handoff-matrix.md](./handoff-matrix.md) | 任务分工矩阵（负责人/排期） | 项目管理 |
| [handoff-checklist.md](./handoff-checklist.md) | 各任务包交付自检清单 | 项目管理 |

**需求来源**

- 飞书：[论文纠错 Agent 前端技术方案](https://ycn0g9jly13e.feishu.cn/wiki/QZBdwEwUiiRteck0WhLcjEs8nBe)
- PRD：[`论文纠错智能Agent产品需求文档.docx`](../../论文纠错智能Agent产品需求文档.docx)

**不在范围**：前端 UI（`apps/web-next`）。

## 推荐阅读顺序（新成员）

1. [backend-api.md](./backend-api.md) — 理解现有 API 与数据模型  
2. [rag-design.md](./rag-design.md) — RAG-1 现状与 RAG-2 设计  
3. [agent-implementation-guide.md](./agent-implementation-guide.md) — 按任务包实施 Agent  
4. [handoff-matrix.md](./handoff-matrix.md) — 认领分工  
5. [model-finetuning.md](./model-finetuning.md) — 微调线（可选并行）
