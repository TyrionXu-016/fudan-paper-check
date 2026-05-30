# 任务分工矩阵

> 在「负责人」「计划开始」「状态」列填写后用于跟踪。预估人天供排期参考。

| 任务包 | 任务 ID | 预估人天 | 建议技能 | 依赖 | 负责人 | 计划开始 | 状态 |
|--------|---------|----------|----------|------|--------|----------|------|
| RAG-2 MVP | R2-1～R2-8 | 5 | Python | SpanBuilder | 赵思远 | 2026-05-30 | 已完成 |
| Agent 基础 | base + llm + filters | 3 | Python | — | 赵思远 | 2026-05-29 | 已完成 |
| Agent-1 | A1-1～A1-7 | 8 | 规则 | RAG-1 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-2 | A2-1～A2-4 | 8 | LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-3 | A3-1～A3-4 | 10 | 规则+LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-4 | A4-1～A4-4 | 8 | LLM | RAG-2, 基础 | 赵思远 | 2026-05-30 | 已完成 |
| Agent-5 编排 | M1～M5 | 5 | 后端 | Agent 1～4 | 赵思远 | 2026-05-30 | 已完成 |
| 后端 API | Phase 2, 3 (SSE, 决策, 导出) | 15 | 后端 | Agent-5 | 第三组(赵思远) | 2026-05-30 | 已完成 |
| 微调基础设施 | FT-0～1 | 10 | ML | — | 第三组(赵思远) | 即将开始 | 待处理 |
| RAG-1 增强 | R1-1～R1-6 | 5 | 规则/后端 | RAG-1 MVP | 第一组 | 待定 | 待认领 |
| 前端 UI | UI-1～UI-4 (SSE接入, 决策) | 10 | 前端 | 后端 API | 第二组 | 待定 | 待认领 |
| 运维部署 | DevOps-1～3 | 3 | 运维 | 所有代码 | 第四组 | 待定 | 待认领 |
| 分任务 LoRA | FT-2～6 | 20 | ML | FT-1 | 第三组(赵思远) | 待定 | 待规划 |

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
