# 交接检查清单（RAG + Agent）

> 负责人认领任务包后，按本清单自检。全部勾选后再提 PR / 交付。

---

## 通用（所有任务包）

- [ ] 阅读 [rag-design.md](./rag-design.md) 与 [agent-implementation-guide.md](./agent-implementation-guide.md)
- [ ] 本地 `PYTHONPATH=packages:apps pytest tests/ -q` 通过
- [ ] 新增代码有对应单元测试
- [ ] 不修改 `/v1/*` 对外 API 契约（除非与 Tech Lead 对齐）
- [ ] 环境变量写入 `deploy/.env.prod.example` 注释说明
- [ ] PR 描述含：任务 ID、验收截图/日志、已知限制

---

## RAG-1 增强（包 R1）

- [ ] `python -m rag.index_rules --all` 成功
- [ ] `GET /v1/rule_bases/generic/retrieve?q=参考文献` 有结果
- [ ] `tests/test_rag.py` 通过或已扩展 fixture
- [ ] 新增规则 MD/YAML 已索引且 source 可追溯

---

## RAG-2（包 B）

- [ ] `build_task_index` 单测通过
- [ ] `retrieve_context` 单测通过
- [ ] Worker 检测完成后 `data/rag/tasks/{task_id}.json` 存在
- [ ] 任务结束后索引清理（TTL 或 drop）
- [ ] `tests/test_doc_retriever.py` 在 CI 通过

---

## Agent-1（包 C）

- [x] `AGENT_MODE=agents` 下 FORMAT/REFERENCE Issue 含 span_id
- [x] RAG-1 检索结果出现在 evidence 或日志（可配置 debug）
- [x] 样例论文回归无严重回归（issue 数 ±20% 内说明原因）

---

## Agent-2（包 D）

- [x] SSE 出现 `TYPO_CHECK`、`GRAMMAR_CHECK`
- [x] LLM JSON 校验 + post_filter 单测
- [x] mock LLM E2E：故意错别字 → suggested_text 正确
- [x] 无 LLM key 时优雅跳过（0 issue + 日志）

---

## Agent-3（包 E）

- [x] 摘要数值不一致 → `logic_contradiction` + span_id
- [x] degraded 文档不调用 LLM
- [x] 图表编号 Issue 与现 checker 一致或更细

---

## Agent-4（包 F）

- [x] `POLISH_ENABLED=false` 跳过润色
- [x] 润色 Issue severity 默认 info
- [x] accept 后 preview 文本变化符合预期

---

## Agent-5 编排（包 G）

- [x] `AGENT_MODE=rules` 与现网行为一致（默认）
- [x] `AGENT_MODE=hybrid` merge 策略单测
- [x] 全 stage SSE E2E 通过
- [x] Docker 部署 worker 日志无未捕获异常

---

## 微调接入（包 FT，见 model-finetuning.md）

- [ ] `FT_ENABLED=false` 走基座 Prompt
- [ ] `ModelRouter` mock 单测
- [ ] FT-5 评测报告归档 `training/eval/reports/`

---

## 部署（DevOps）

- [ ] `./deploy/deploy.sh` 或等价流程可重复部署
- [ ] 生产 `curl -H "Host: pager-api.tyrion.space" http://114.55.139.240/health` OK
- [ ] Worker 连接 Redis，异步任务非 inline

---

## 文档

- [ ] 认领任务在 [handoff-matrix.md](./handoff-matrix.md) 填写负责人与日期
- [ ] 重大设计偏差更新 rag-design / agent-implementation-guide
