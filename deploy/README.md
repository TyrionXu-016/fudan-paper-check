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

```bash
ssh root@114.55.139.240
certbot certonly --nginx -d pager-api.tyrion.space
# 然后按 deploy/nginx/pager-api.tyrion.space.conf 内注释启用 443 块
nginx -t && systemctl reload nginx
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

`deploy/.env.prod`（已在服务器生成，勿提交 Git）：

- `JWT_SECRET` — 生产 JWT 密钥
- `CORS_ORIGINS` — 允许的前端来源
- `PDF_CONVERTER_MODE=mock` — PDF 转换 mock（未部署 maker/mineru 镜像时）

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
