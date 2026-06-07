# 后端生产部署说明

## 服务器信息

| 项 | 值 |
|----|-----|
| SSH | `ssh mse` |
| 服务器路径 | `/opt/fudan-pager-check-mse` |
| 部署分支 | `mse-tyrion` |
| API 容器端口 | `127.0.0.1:18083` -> 8000 |
| 后端域名 | `api-mse.tyrion.space` |
| 服务器 IP | `114.55.139.240` |

这是一套独立的第二项目部署，不复用 `/opt/fudan-pager-check`，不占用旧服务的 `18082` 端口，也不修改旧域名的 Nginx 配置。

## DNS

Nginx 可先按 Host 头代理。DNS 生效前在 `tyrion.space` 控制台添加：

| 类型 | 主机记录 | 记录值 |
|------|----------|--------|
| A | `api-mse` | `114.55.139.240` |

生效后访问：`http://api-mse.tyrion.space/health`。

## Git Pull 部署

部署不再使用 rsync。服务器在 `/opt/fudan-pager-check-mse` 保留第二套 Git 仓库，脚本只做 `git fetch`/`git pull --ff-only`、重建 Docker 镜像、重启 MSE 后端服务：

```bash
./deploy/deploy.sh
```

服务器上手动执行：

```bash
cd /opt/fudan-pager-check-mse
DEPLOY_BRANCH=mse-tyrion ./deploy/git-pull-deploy.sh
```

## 自动部署

`deploy/install-auto-deploy.sh` 安装 systemd timer，每 60 秒检查一次 `origin/mse-tyrion`。当前分支有新提交并推送后，服务器自动 `git pull` 并重新部署后端。

```bash
cd /opt/fudan-pager-check-mse
DEPLOY_BRANCH=mse-tyrion ./deploy/install-auto-deploy.sh
systemctl list-timers --all fudan-pager-check-mse-autodeploy.timer --no-pager
journalctl -u fudan-pager-check-mse-autodeploy.service -n 80 --no-pager
```

## Docker 服务

```bash
cd /opt/fudan-pager-check-mse
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.prod ps
docker logs -f fudan-pager-mse-api-1
docker logs -f fudan-pager-mse-worker-1
curl http://127.0.0.1:18083/health
curl -H "Host: api-mse.tyrion.space" http://127.0.0.1/health
```

组件：

- `fudan-pager-mse-api-1` - FastAPI
- `fudan-pager-mse-worker-1` - arq 异步任务
- `fudan-pager-mse-redis-1` - Redis 队列

## 环境变量

`deploy/.env.prod` 只保存在服务器，勿提交 Git。完整模板见 [`deploy/.env.prod.example`](.env.prod.example)。

部署脚本会自动准备：

- `JWT_SECRET`、`MSE_INVITE_SECRET`
- `MSE_DATABASE_URL=sqlite:////app/data/mse.db`
- `PDF_CONVERTER_MODE=docker`
- `MSE_ALLOW_MOCK_FALLBACK=0`
- `MINERU_IMAGE=fudan-pager-mse-mineru`
- `MAKER_IMAGE=fudan-pager-mse-maker`
- `CORS_ORIGINS` 追加 `api-mse.tyrion.space`

飞书/企业微信 Webhook 可暂不配置。DeepSeek、SMTP 如需 live 能力，在服务器 `deploy/.env.prod` 中配置 `LLM_API_KEY`、`NOTIFIER=smtp` 和 `SMTP_*` 后重新运行部署脚本。

## HTTPS

DNS 解析到 `114.55.139.240` 后，在服务器执行：

```bash
cd /opt/fudan-pager-check-mse
./deploy/setup-https.sh
```

该脚本会申请 `api-mse.tyrion.space` 证书，切换到 HTTPS Nginx 配置，并验证 `/health`。
