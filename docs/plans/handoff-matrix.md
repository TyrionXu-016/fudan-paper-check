# 任务分工矩阵

> 在「负责人」「计划开始」「状态」列填写后用于跟踪。预估人天供排期参考。

| 任务包 | 任务 ID | 预估人天 | 建议技能 | 依赖 | 负责人 | 计划开始 | 状态 |
|--------|---------|----------|----------|------|--------|----------|------|
| RAG-1 知识库清洗与构建 | R1 | Markdown/数据工程 | 第二组(王诗琪/尚国瑞) | 2026-05-20 | 已完成 |
| 前端 UI 开发 | UI | Vue3/Pinia | 第四组(黄婧雯) | 2026-05-20 | 已完成 |
| 基础后端与架构搭建 | Backend | FastAPI | 架构侧/基础底座 | 2026-05-20 | 已完成 |
| Agent 智能流水线与 API 集成 | Agent 1~5 | 算法工程 | 第三组(赵思远/徐阳) | 2026-05-29 | 已完成 |
| 微调数据集构造 | FT-1 | LLM/Prompt | 第三组(赵思远/徐阳) | 即将开始 | 待处理 |
| 垂直任务 LoRA 微调训练 | FT-2~6 | ML/微调 | 第三组(赵思远/徐阳) | 待定 | 待规划 |
| 里程碑统筹与整体测试评测 | PM | 测试/产品 | 第一组(管慧君) | 2026-05-20 | 进行中 |

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
