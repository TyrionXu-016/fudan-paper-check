# fudan-pager-check

论文预检查 Agent 系统：PDF/MD 双源解析 → 统一文档模型 → 四类检查 → REST API 报告。

## 架构

- `packages/schema` — PaperDocument / Issue / CheckReport 模型
- `packages/parser` — DualSourceFusionParser（maker 主 + mineru 辅）
- `packages/checks` — structure / format / reference / consistency
- `packages/orchestrator` — 检查编排与报告生成
- `apps/web-next` — **Next.js 独立前端**（登录、历史任务、上传、报告详情）
- `apps/web` — 旧版静态页（API 托管，可选）
- `apps/api` — FastAPI 异步任务接口 + JWT 认证

## 实施计划

后端 API、Agent 流水线、模型微调的分模块计划见 [`docs/plans/`](docs/plans/README.md)。

- [后端 API 实施计划](docs/plans/backend-api.md)（当前优先）
- [Agent 流水线计划](docs/plans/agent-pipeline.md)
- [模型微调计划](docs/plans/model-finetuning.md)

## 快速开始

### 1. 后端 API

```bash
python3 -m pip install pydantic pyyaml httpx fastapi "uvicorn[standard]" python-multipart arq redis eval_type_backport pyjwt pytest
export PYTHONPATH=packages:apps
python3 -m uvicorn api.main:app --reload --app-dir apps
```

默认地址：http://localhost:8000

### 2. Next.js 前端（推荐）

```bash
cd apps/web-next
cp .env.local.example .env.local
npm install
npm run dev
```

浏览器打开 http://localhost:3000

- `/register` 注册账号
- `/login` 登录
- `/dashboard` 历史任务列表
- `/upload` 上传论文
- `/jobs/{id}` 查看报告

### 3. 测试

```bash
PYTHONPATH=packages:apps python3 -m pytest
```

### 旧版静态页（可选）

```bash
export PYTHONPATH=packages:apps
python3 -m uvicorn api.main:app --reload --app-dir apps
```

浏览器打开 http://localhost:8000（需自行在请求中带 JWT，建议使用 Next 前端）

### API（curl，需登录 token）

```bash
# 注册
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"secret12","name":"Demo"}'

# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"secret12"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 上传 maker + mineru
curl -X POST http://localhost:8000/v1/papers \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/基于集成深度学习模型的公路隧道交通流预测_钱超_maker.md" \
  -F "mineru_file=@samples/基于集成深度学习模型的公路隧道交通流预测_钱超_mineru.md"

# 历史任务列表
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/papers

# 查询状态与报告
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/papers/{job_id}
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/papers/{job_id}/report
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/papers/{job_id}/report.md
```

### Docker Compose

```bash
docker compose up --build
```

### PDF 转换（Phase 2）

设置环境变量启用 Docker 转换器：

```bash
export MAKER_IMAGE=fudan-pager-maker
export MINERU_IMAGE=fudan-pager-mineru
export PDF_CONVERTER_MODE=docker
```

构建 stub 镜像：

```bash
docker build -f docker/maker/Dockerfile -t fudan-pager-maker .
docker build -f docker/mineru/Dockerfile -t fudan-pager-mineru .
```

### LLM 一致性检查（可选）

```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini
```

未配置 API Key 时自动使用规则版摘要覆盖检查。

## 期刊模板

`config/journals/scut_natural_science.yaml` — 华南理工大学学报（自然科学版）

## 样本数据

`samples/` 目录包含 maker/mineru 样例及架构分析文档。
