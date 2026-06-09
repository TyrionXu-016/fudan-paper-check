# 后端生产部署说明

## 服务器信息

| 项 | 值 |
|----|-----|
| SSH | `ssh mse` |
| 服务器路径 | `/opt/fudan-pager-check-mse` |
| 部署分支 | `mse-tyrion` |
| API 容器端口 | `127.0.0.1:18083` -> 8000 |
| 后端域名 | `api-mse.tyrion.space` |
| 前端域名 | `mse.paper.tyrion.space` |
| 服务器 IP | `114.55.139.240` |

这是一套独立的第二项目部署，不复用 `/opt/fudan-pager-check`，不占用旧服务的 `18082` 端口，也不修改旧域名的 Nginx 配置。

## DNS

Nginx 可先按 Host 头代理。DNS 生效前在 `tyrion.space` 控制台添加：

| 类型 | 主机记录 | 记录值 |
|------|----------|--------|
| A | `api-mse` | `114.55.139.240` |

生效后访问：`http://api-mse.tyrion.space/health`。

## 预构建镜像部署

生产机内存较小，不再现场 `docker build` 或 `pip install`。应用镜像必须先在本地或构建机预构建为 `linux/amd64`，上传到服务器 `docker load`，再由服务器无构建重启容器。

```bash
DEPLOY_BRANCH=mse-tyrion ./deploy/release-prebuilt-app.sh
```

如果 Docker Hub 访问不稳定，可临时指定兼容镜像源：

```bash
PYTHON_IMAGE=public.ecr.aws/docker/library/python:3.12-slim \
  DEPLOY_BRANCH=mse-tyrion ./deploy/release-prebuilt-app.sh
```

该脚本会：

1. 构建 `fudan-pager-mse-app:<git_sha>`。
2. `docker save | gzip` 后通过 `scp` 上传到 `ssh mse`。
3. 在服务器执行 `docker load`。
4. 写入 `deploy/.env.prod` 的 `APP_IMAGE`。
5. 运行 `deploy/git-pull-deploy.sh`，只 `docker compose up -d --no-build`。

服务器上仅重启已加载镜像：

```bash
cd /opt/fudan-pager-check-mse
DEPLOY_BRANCH=mse-tyrion ./deploy/git-pull-deploy.sh
```

转换镜像仅在首次初始化或 Dockerfile 变化时单独构建：

```bash
cd /opt/fudan-pager-check-mse
./deploy/build-converter-images.sh
```

`deploy/git-pull-deploy.sh` 会校验 `APP_IMAGE`、`MAKER_IMAGE`、`MINERU_IMAGE` 已在服务器本地存在。缺镜像时会直接失败，不会在生产机上 fallback build。

## 自动部署

`deploy/install-auto-deploy.sh` 默认只安装 unit 并保持 timer 禁用，避免轮询分支后在未预加载镜像的情况下重启失败。预构建发布流程稳定后，可以显式启用：

```bash
cd /opt/fudan-pager-check-mse
ENABLE_AUTO_DEPLOY=1 DEPLOY_BRANCH=mse-tyrion ./deploy/install-auto-deploy.sh
systemctl list-timers --all fudan-pager-check-mse-autodeploy.timer --no-pager
journalctl -u fudan-pager-check-mse-autodeploy.service -n 80 --no-pager
```

启用后仍要求服务器已有 `APP_IMAGE` 指向的镜像；自动部署不会现场构建。

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

## 公网验收记录

最近一次公网验收见 [`docs/plans/public-acceptance-2026-06-08.md`](../docs/plans/public-acceptance-2026-06-08.md)。该次验收发现前端与基础 API 可达，但 PDF 上传后生产解析链路进入 `parse_failed`，并导致 API `/health` 多次超时；修复 worker/Redis/inline fallback 后需按该文档复测。

## 环境变量

`deploy/.env.prod` 只保存在服务器，勿提交 Git。完整模板见 [`deploy/.env.prod.example`](.env.prod.example)。

部署脚本会自动准备：

- `JWT_SECRET`、`MSE_INVITE_SECRET`
- `APP_IMAGE=fudan-pager-mse-app:<git_sha>`（由 `release-prebuilt-app.sh` 写入）
- `MSE_DATABASE_URL=sqlite:////app/data/mse.db`
- `PDF_CONVERTER_MODE=docker`
- `MSE_ALLOW_MOCK_FALLBACK=0`
- `MINERU_IMAGE=fudan-pager-mse-mineru`
- `MAKER_IMAGE=fudan-pager-mse-maker`
- `APP_BASE_URL=https://mse.paper.tyrion.space`
- `CORS_ORIGINS` 追加 `api-mse.tyrion.space` 和 `mse.paper.tyrion.space`

飞书/企业微信 Webhook 可暂不配置。DeepSeek、SMTP 如需 live 能力，在服务器 `deploy/.env.prod` 中配置 `LLM_API_KEY`、`NOTIFIER=smtp` 和 `SMTP_*` 后重新运行部署脚本。

## 资源要求

当前 MSE 机器约 1.7GiB 内存，只适合运行已构建好的 API/Worker/Redis 和转换容器，不适合同时执行应用镜像 build、MinerU build 或依赖安装。若要稳定处理真实 PDF，建议至少升级后端机器，或拆分 API 与 worker/converter。

## HTTPS

DNS 解析到 `114.55.139.240` 后，在服务器执行：

```bash
cd /opt/fudan-pager-check-mse
./deploy/setup-https.sh
```

该脚本会申请 `api-mse.tyrion.space` 证书，切换到 HTTPS Nginx 配置，并验证 `/health`。
