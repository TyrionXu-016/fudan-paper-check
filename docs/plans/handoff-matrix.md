# 任务分工矩阵

> 在「负责人」「计划开始」「状态」列填写后用于跟踪。预估人天供排期参考。

| 任务包 | 任务 ID | 预估人天 | 建议技能 | 依赖 | 负责人 | 计划开始 | 状态 |
|--------|---------|----------|----------|------|--------|----------|------|
| RAG-1 增强 | R1-1～R1-6 | 5 | 规则/后端 | RAG-1 MVP | 赵思远 | 2026-05-30 | 已完成 |
| RAG-2 MVP | R2-1～R2-8 | 5 | Python | SpanBuilder | 赵思远 | 2026-05-30 | 已完成 |
| Agent 基础 | base + llm + filters | 3 | Python | — | LeoSian(赵思远) | 2026-05-29 | 已完成 |
| Agent-1 | A1-1～A1-7 | 8 | 规则 | RAG-1 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-2 | A2-1～A2-4 | 8 | LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-3 | A3-1～A3-4 | 10 | 规则+LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-4 | A4-1～A4-4 | 8 | LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-5 编排 | M1～M5 | 5 | 后端 | Agent 1～4 | 赵思远 | 2026-05-30 | 已完成 |
| E2E 测试 | 包 H | 3 | QA | Agent-5 | | | 待认领 |
| 微调 FT-0～6 | 见 model-finetuning.md | 30+ | ML | 可与 Agent 并行 | 第三组(赵思远/徐阳) | 2026-05-30 | 进行中 |

## 推荐里程碑

| 里程碑 | 包含任务包 | 目标日期（示例） |
|--------|------------|------------------|
| M1 | Agent 基础 + Agent-1 + RAG-1 R1-2 | +2 周 |
| M2 | RAG-2 + Agent-2 | +4 周 |
| M3 | Agent-3 | +6 周 |
| M4 | Agent-4 + Agent-5 + E2E | +8 周 |
| M5 | RAG 向量可选 + FT-6 接入 | +10 周 |

## 文档索引

- 设计：[rag-design.md](./rag-design.md)、[agent-implementation-guide.md](./agent-implementation-guide.md)
- 总览：[agent-pipeline.md](./agent-pipeline.md)、[model-finetuning.md](./model-finetuning.md)
- 交接：[handoff-checklist.md](./handoff-checklist.md)
