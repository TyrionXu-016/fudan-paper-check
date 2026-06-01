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
| `MSE_INVITE_SECRET` | 随机串 | 邀请 token HMAC |
| `NOTIFIER` | `smtp` | 邮件：`console` 仅日志 |
| `LLM_API_KEY` | DeepSeek Key | 未配置时 Agent 跳过 |

### 数据卷布局（`pager_data` → `/app/data`）

```
/app/data/
  mse.db                 # MSE SQLite（含 WAL 文件）
  uploads/{job_id}/      # 学生论文上传
  rag/mse/{project_id}/  # 规范文档 sources + index.json
  users.json             # 用户（过渡期）
```

API 与 Worker **必须**挂载同一 `pager_data` 卷；Worker 额外挂载 `/var/run/docker.sock` 以运行 MinerU 容器。

### MSE 本地验收

```bash
# 开发（允许 mock）
MSE_ALLOW_MOCK_FALLBACK=1 JOB_RUN_INLINE=1 ./scripts/mse_acceptance.sh

# 生产前（需 MinerU 镜像 + docker.sock）
MSE_ALLOW_MOCK_FALLBACK=0 PDF_CONVERTER_MODE=docker ./scripts/mse_acceptance_full.sh
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
