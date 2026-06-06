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

- [硕士学位论文辅导系统](docs/plans/mse-tutoring-system.md)（分支 `mse-tyrion`，当前优先）
- [后端 API 实施计划](docs/plans/backend-api.md)（已完成）
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

真实 PDF 样例：

```bash
./scripts/download_real_pdf_samples.sh
./scripts/download_mse_public_thesis_pdf.sh
# 见 samples/real_pdfs/README.md
```

开发默认 `PDF_CONVERTER_MODE=mock`、`MSE_ALLOW_MOCK_FALLBACK=1`。启用 MinerU 严格模式：

```bash
export PDF_CONVERTER_MODE=docker
export MSE_ALLOW_MOCK_FALLBACK=0
export MINERU_IMAGE=fudan-pager-mineru
export MAKER_IMAGE=fudan-pager-maker
docker compose up --build api worker redis
```

Worker 需能访问 Docker（Compose 已挂载 `docker.sock`）。

### MSE 论文辅导系统

本地开发（inline worker + mock 解析）：

```bash
export JOB_RUN_INLINE=1
export MSE_ALLOW_MOCK_FALLBACK=1
export PYTHONPATH=packages:apps
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --app-dir apps

cd apps/web-next && npm run dev
```

- 导师/学生入口：http://localhost:3000/mse/dashboard
- 验收脚本：`./scripts/mse_acceptance.sh`（mock） / `./scripts/mse_acceptance_full.sh`（扩展） / `./scripts/mse_acceptance_quasi_prod.sh`（本地准生产，无 SKIP）

生产部署见 [`deploy/README.md`](deploy/README.md)。

### PDF 转换（Phase 2）

设置环境变量启用 Docker 转换器：

```bash
export MAKER_IMAGE=fudan-pager-maker
export MINERU_IMAGE=fudan-pager-mineru
export PDF_CONVERTER_MODE=docker
export MSE_ALLOW_MOCK_FALLBACK=0
export MINERU_CACHE_VOLUME=fudan-pager-mineru-cache
export MINERU_METHOD=txt  # born-digital public thesis; scanned PDFs can use auto/ocr
export MINERU_START_PAGE=0
export MINERU_END_PAGE=7
```

构建本地准生产转换镜像：

```bash
docker build -f docker/maker/Dockerfile -t fudan-pager-maker .
docker build -f docker/mineru/Dockerfile -t fudan-pager-mineru .
```

MinerU pipeline 首次运行会下载模型并处理较慢；默认 `MINERU_CACHE_VOLUME=fudan-pager-mineru-cache` 会挂载到容器 `/root/.cache`，后续验收复用 Docker volume 缓存。本地准生产脚本会下载完整公开硕士论文 PDF，并默认通过 `MINERU_START_PAGE=0` / `MINERU_END_PAGE=7` 让 Maker 与 MinerU 都只转换前 8 页，避免本机 Docker OCR/LLM 阶段因整本论文资源波动而不稳定；生产全文转换时不要设置页码窗口。

公开样本固定为 Dartmouth Digital Commons 的 “Chinese Font Style Transfer with Neural Network”。下载器只接受 Dartmouth 页面解析出的 PDF，并会校验题名/作者/学校标识；如果站点触发 WAF challenge，可在浏览器中从 <https://digitalcommons.dartmouth.edu/masters_theses/24/> 手动下载 PDF，再导入到准生产固定路径：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_import_public_thesis_pdf.py ~/Downloads/Chinese-Font-Style-Transfer.pdf
```

本地准生产验收会强制使用 Docker 转换、真实公开硕士论文 PDF、DeepSeek 与 SMTP：

```bash
cp .env.example .env
# 填写 LLM_API_KEY、NOTIFIER=smtp、SMTP_*、SMTP_TEST_STU
PYTHONPATH=packages:apps python3 scripts/mse_config_status.py --quasi-prod-only
./scripts/mse_acceptance_quasi_prod.sh
```

`mse_config_status.py` 会合并当前环境与 `.env`；默认统一检查准生产 DeepSeek/SMTP/strict converter、Dartmouth 公开 PDF、CNKI/机构样本、飞书/企业微信 live webhook 配置。`--quasi-prod-only` 只检查 `mse_acceptance_quasi_prod.sh` 实际要跑的 DeepSeek/SMTP/strict converter 与 Dartmouth 公开 PDF。输出 `CONFIG_REQUIRED` 时退出码为 2，且不会打印 key、密码或 webhook URL。

修订截止提醒可由 cron 或 systemd timer 调用；默认第 1 轮问题发布后 7 天截止，并在截止前 24 小时提醒一次：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_revision_reminders.py
```

除 SMTP 外，也可把通知发到飞书或企业微信群机器人：

```bash
export NOTIFIER=webhook
export WEBHOOK_KIND=feishu  # 或 wecom
export WEBHOOK_URL=https://...
```

本地无外部 webhook 时，可以先跑本地捕获验收：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_acceptance_webhook.py
```

CNKI/机构样本集下载到本地后，用导入脚本校验并写入 manifest 指向的位置：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_import_private_sample.py \
  --pdf ~/Downloads/cnki-thesis.pdf \
  --spec ~/Downloads/school-spec.pdf \
  --school "Example University" \
  --subfield software_engineering
```

导入完成后，用 manifest 检查器确认 M1-5 输入齐备：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_check_sample_manifest.py --require-primary
# 或一次性查看全部外部配置缺口
PYTHONPATH=packages:apps python3 scripts/mse_config_status.py
```

API 已按准生产方式启动后，可跑私有样本 live 验收：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_acceptance_private_samples.py
```

配置真实群机器人后，可跑 webhook live 验收：

```bash
WEBHOOK_KIND=feishu WEBHOOK_URL=https://... \
  PYTHONPATH=packages:apps python3 scripts/mse_acceptance_webhook_live.py
```

Webhook live 验收会先检查 `WEBHOOK_URL` 是否为 `http/https` URL；发送失败时只输出失败阶段和错误类型，不打印完整群机器人 URL。

所有外部配置都齐备后，可以跑最终 live 聚合验收；它会先运行完整配置总检，再串起本地准生产、CNKI/机构私有样本 live、webhook live：

```bash
./scripts/mse_acceptance_final_live.sh
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
