# 生产部署说明

## 服务器信息

| 项 | 值 |
|----|-----|
| 路径 | `/opt/fudan-pager-check` |
| API 容器端口 | `127.0.0.1:18082` → 8000 |
| 域名（待 DNS） | `pager-api.tyrion.space` |

## 需要你配置的 DNS

在 `tyrion.space` 域名控制台添加：

| 类型 | 主机记录 | 记录值 |
|------|----------|--------|
| A | `pager-api` | `114.55.139.240` |

解析生效后访问：`http://pager-api.tyrion.space/v1/rule_bases`

## HTTPS（DNS 生效后执行）

**前提**：权威 DNS 能解析到服务器 IP：

```bash
dig @dns17.hichina.com pager-api.tyrion.space A
# 应返回 114.55.139.240
```

在服务器上一键配置（已上传 `deploy/setup-https.sh`）：

```bash
ssh root@114.55.139.240
/opt/fudan-pager-check/deploy/setup-https.sh
```

或手动：

```bash
certbot certonly --nginx -d pager-api.tyrion.space --non-interactive --agree-tos
cp /opt/fudan-pager-check/deploy/nginx/pager-api.tyrion.space.conf /etc/nginx/conf.d/
nginx -t && systemctl reload nginx
curl https://pager-api.tyrion.space/health
```

## 常用运维命令

```bash
cd /opt/fudan-pager-check

# 查看状态
docker compose -f deploy/docker-compose.prod.yml ps

# 重新部署（本地 rsync 后）
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.prod up -d --build

# 日志
docker logs -f deploy-api-1
docker logs -f deploy-worker-1

# 健康检查
curl http://127.0.0.1:18082/health
curl -H "Host: pager-api.tyrion.space" http://127.0.0.1/v1/rule_bases
```

## 环境变量

`deploy/.env.prod`（已在服务器生成，勿提交 Git）。完整模板见 [`deploy/.env.prod.example`](.env.prod.example)。

### 通用

| 变量 | 说明 |
|------|------|
| `JWT_SECRET` | 生产 JWT 密钥（≥32 字符） |
| `CORS_ORIGINS` | 允许的前端来源（含 Next.js 域名） |
| `APP_BASE_URL` | 前端根 URL，用于邮件/邀请链接 |

### MSE 辅导系统

| 变量 | 生产推荐值 | 说明 |
|------|------------|------|
| `MSE_DATABASE_URL` | `sqlite:////app/data/mse.db` | SQLite 绝对路径（四斜杠） |
| `PDF_CONVERTER_MODE` | `docker` | 论文/规范 PDF 走 MinerU |
| `MSE_ALLOW_MOCK_FALLBACK` | `0` | 禁用样例 MD 回退 |
| `MINERU_IMAGE` / `MAKER_IMAGE` | 自建镜像名 | Worker 通过 docker.sock 调用 |
| `MINERU_BACKEND` / `MINERU_METHOD` | `pipeline` / `auto` | MinerU CLI 后端与解析方法；born-digital 验收样本可用 `txt` |
| `MINERU_TIMEOUT_SECONDS` | `1800` | 真实论文首次转换和模型冷启动超时 |
| `MINERU_CACHE_VOLUME` | `fudan-pager-mineru-cache` | 挂载到 MinerU 容器 `/root/.cache` 的 Docker 模型缓存 |
| `MINERU_CACHE_DIR` | 可选 | 显式宿主目录缓存；未设置时使用 `MINERU_CACHE_VOLUME` |
| `MINERU_START_PAGE` / `MINERU_END_PAGE` | 生产留空 | 本地准生产验收可限制公开论文页码窗口；Maker 与 MinerU 都会使用该窗口，生产全文转换不要设置 |
| `MINERU_PDF_RENDER_THREADS` / `MINERU_PROCESSING_WINDOW_SIZE` | 生产按机器调整 | MinerU 渲染并发和处理窗口；本地验收默认降到 `1` / `8` |
| `MINERU_FORMULA_ENABLE` / `MINERU_TABLE_ENABLE` | 生产按需求启用 | 本地验收可关闭以降低模型负载 |
| `MSE_INVITE_SECRET` | 随机串 | 邀请 token HMAC |
| `NOTIFIER` | `smtp` | 通知：`smtp` / `webhook` / `console` |
| `WEBHOOK_KIND` / `WEBHOOK_URL` | 可选 | `NOTIFIER=webhook` 时使用；支持 `feishu` / `wecom` 群机器人 |
| `MSE_REVISION_DUE_DAYS` | `7` | 学生收到问题后默认修改截止天数 |
| `MSE_REVISION_REMINDER_WINDOW_HOURS` | `24` | 截止前多少小时发送一次提醒 |
| `LLM_API_KEY` | DeepSeek Key | 未配置时 Agent 跳过 |

### 数据卷布局（`pager_data` → `/app/data`）

```
/app/data/
  mse.db                 # MSE SQLite（含 WAL 文件）
  uploads/{job_id}/      # 学生论文上传
  rag/mse/{project_id}/  # 规范文档 sources + index.json
  users.json.bak-*       # 旧 JSON 用户迁移前备份（如存在）
```

API 与 Worker **必须**挂载同一 `pager_data` 卷；Worker 额外挂载 `/var/run/docker.sock` 以运行 MinerU 容器。

### MSE 本地验收

```bash
# 开发（允许 mock）
MSE_ALLOW_MOCK_FALLBACK=1 JOB_RUN_INLINE=1 ./scripts/mse_acceptance.sh

# 本地准生产（需真实 MinerU 镜像、DeepSeek、SMTP、公开论文 PDF；不允许 SKIP）
PYTHONPATH=packages:apps python3 scripts/mse_config_status.py --quasi-prod-only
./scripts/mse_acceptance_quasi_prod.sh

# 公开 PDF 固定为 Dartmouth “Chinese Font Style Transfer with Neural Network”；
# 若 Digital Commons 返回 WAF challenge，请手动下载后用导入脚本校验并复制：
# PYTHONPATH=packages:apps python3 scripts/mse_import_public_thesis_pdf.py ~/Downloads/Chinese-Font-Style-Transfer.pdf

# 截止提醒（放入 cron/systemd timer）
PYTHONPATH=packages:apps python3 scripts/mse_revision_reminders.py

# Webhook 本地端到端验收（无需真实飞书/企业微信 URL）
PYTHONPATH=packages:apps python3 scripts/mse_acceptance_webhook.py

# Webhook live 验收（需真实群机器人 URL）
WEBHOOK_KIND=feishu WEBHOOK_URL=https://... \
  PYTHONPATH=packages:apps python3 scripts/mse_acceptance_webhook_live.py
# 失败时只输出阶段和错误类型，不打印完整 WEBHOOK_URL

# 最终 live 聚合验收（需所有外部配置齐备）
./scripts/mse_acceptance_final_live.sh

# CNKI/机构样本齐备性检查（配置样本后运行）
PYTHONPATH=packages:apps python3 scripts/mse_import_private_sample.py \
  --pdf ~/Downloads/cnki-thesis.pdf \
  --spec ~/Downloads/school-spec.pdf \
  --school "Example University" \
  --subfield software_engineering
PYTHONPATH=packages:apps python3 scripts/mse_check_sample_manifest.py --require-primary

# 全部外部配置总检；缺配置时返回 2，不打印 secrets 或 webhook URL
PYTHONPATH=packages:apps python3 scripts/mse_config_status.py

# CNKI/机构样本 API 验收（需 API 已按准生产方式启动）
PYTHONPATH=packages:apps python3 scripts/mse_acceptance_private_samples.py
```

## 一键部署（本地）

```bash
export DEPLOY_SSH_PASSWORD='你的服务器密码'
./deploy/deploy.sh
```

或手动 rsync + compose（`deploy/.env.prod` 已在服务器保留，勿被 rsync --delete 覆盖）：

## 组件

- `deploy-api-1` — FastAPI
- `deploy-worker-1` — arq 异步任务
- `deploy-redis-1` — 任务队列（仅内网）

Nginx 配置：`/etc/nginx/conf.d/pager-api.tyrion.space.conf`
