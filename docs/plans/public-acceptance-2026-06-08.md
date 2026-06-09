# 公网部署验收记录（2026-06-08）

## 目标

验证当前公网部署的最小可用链路：

- 后端 API：`https://api-mse.tyrion.space`
- 前端：`https://mse.paper.tyrion.space`
- MSE 关键流程：注册导师/学生、创建项目、默认规范索引、邀请绑定、PDF 上传、报告状态、导出。

## 环境与测试数据

执行时间：2026-06-08 21:08-21:28 CST。

测试方式：

- `curl` 检查公网 HTTP/HTTPS 可达性。
- `httpx` 调用公网 API 执行业务闭环。
- headless Chromium 渲染前端登录页并生成截图。

临时测试 PDF：

- 路径：`/tmp/codex-public-acceptance-thesis.pdf`
- 大小：3182 bytes
- 页数：2
- 生成方式：本地 `reportlab` 生成，仅用于公网上传链路 smoke test。

说明：本次未使用 CNKI/中国期刊网私有硕士论文样本。`scripts/download_mse_public_thesis_pdf.sh` 尝试下载 Dartmouth 公开硕士论文时，目标站点返回 `HTTP 403 Forbidden`，与既有文档中 WAF 说明一致。因此本次不替代 M1-5 CNKI/机构样本验收。

## 测试账号与对象

- 导师账号：`codex-public-acceptance-20260608-211027-1d8573-advisor@example.test`
- 学生账号：`codex-public-acceptance-20260608-211027-1d8573-student@example.test`
- 项目标题：`codex-public-acceptance-20260608-211027-1d8573`
- 项目 ID：`1f5017f4-3b4f-462a-be6b-dd9d26af9298`
- 第 1 轮 ID：`92b5614e-50e3-4457-bfcf-abca7aa33dc4`
- Job ID：`a89f7425-e6f8-4f02-89d7-095d7d02d900`

## 通过项

### 公网入口

- `GET https://api-mse.tyrion.space/health` 初始返回 `HTTP 200`，响应体为 `{"status":"ok"}`。
- `GET https://mse.paper.tyrion.space/login` 返回 `HTTP 200`。
- `GET https://mse.paper.tyrion.space/register` 返回 `HTTP 200`。
- `GET https://mse.paper.tyrion.space/mse/dashboard` 返回 `HTTP 200`。
- `GET https://mse.paper.tyrion.space/mse/projects/new` 返回 `HTTP 200`。
- headless Chromium 渲染 `/login` 后可见登录表单字段：`邮箱`、`密码`、`进入工作台`。

截图证据保存在本机临时目录：

- `/tmp/fudan_public_login.png`
- `/tmp/fudan_public_login_mobile.png`

### 账号、项目与邀请

- 导师注册成功。
- 学生注册成功。
- 导师创建项目成功，返回默认规则库：`rule-default-1fe8bb7d`。
- 邀请链接生成成功，返回前端公网域名：
  `https://mse.paper.tyrion.space/mse/invite/_9UESPgP1DVrq9boADyDZQ.09e40381281c122bd35a7161e1de9517`
- 学生接受邀请成功。
- 导师 dashboard API 返回 `HTTP 200`，可见项目统计。

### 失败态可观测性

PDF 上传请求客户端超时后，后续查询确认服务端已创建第 1 轮。导师 dashboard 能看到 `parse_failed` todo。

`GET /v1/mse/projects/{project_id}/rounds/1/report`：

- 导师返回 `HTTP 200`
- 学生返回 `HTTP 200`
- `review_status` 为 `parse_failed`
- `report` 为 `null`

导出接口在 `parse_failed` 状态下仍可返回空报告文件：

- `GET /export.md` 返回 `HTTP 200`，大小 139 bytes。
- `GET /export.pdf` 返回 `HTTP 200`，响应以 `%PDF` 开头，大小 2558 bytes。

## 失败项

### P0：公网 PDF 上传分析链路失败

上传临时真实 PDF 后，客户端等待 120 秒后超时。随后查询项目轮次，服务端已创建第 1 轮，但最终状态为 `parse_failed`。

dashboard 活动日志中的失败信息：

```text
PDF conversion requires docker (PDF_CONVERTER_MODE=docker) or MSE_ALLOW_MOCK_FALLBACK=1 for local dev
```

这说明生产上传没有成功进入可执行 Docker 转换的 worker 路径，而是落入 API 进程 inline fallback。API 容器没有 Docker 转换能力，导致解析失败。

需要在服务器侧优先检查：

- `fudan-pager-mse-worker-1` 是否正常运行。
- API 容器到 Redis 的连接是否正常。
- `arq` 任务是否成功入队。
- worker 容器是否挂载 `/var/run/docker.sock`，并能执行 `fudan-pager-mse-maker` / `fudan-pager-mse-mineru`。
- API 进程是否应在生产 strict 模式下禁止 inline fallback，避免长时间阻塞请求。

### P0：上传后 API 可用性明显下降

PDF 上传后，后续多次 `GET /health` 出现超时：

```text
attempt=1 HTTP=000 time_total=10.002007
attempt=2 HTTP=000 time_total=10.004422
attempt=3 HTTP=000 time_total=10.002536
attempt=4 HTTP=000 time_total=10.005493
attempt=5 HTTP=000 time_total=10.006382
```

同一时间段前端 Vercel 路由仍可快速返回 `HTTP 200`，问题集中在后端 API 服务。

恢复观察：文档记录完成前再次执行短超时 health check，`GET https://api-mse.tyrion.space/health` 恢复为 `HTTP 200`，`time_total=0.153521`。因此该问题表现为 PDF 上传/解析触发的服务不可用窗口，而不是持续离线。

## 结论

本次公网验收未通过。

公网前端可访问，基础账号/项目/邀请 API 可工作；但 PDF 上传后的生产解析链路失败，并且上传期间 API 健康检查出现持续超时。当前部署不能视为 MSE 上传分析流程可用。

## 修复记录

执行时间：2026-06-08 21:45-22:30 CST。

根因定位：

- API 日志显示上传期间出现 `redis connection error redis:6379` 与 DNS 临时解析失败，API 入队失败后落入 inline fallback。
- 生产配置为 `PDF_CONVERTER_MODE=docker`、`MSE_ALLOW_MOCK_FALLBACK=0`，但 API 容器不具备 Docker 转换能力，因此 inline 处理触发 `PDF conversion requires docker ...`。
- worker 容器虽然能连接 Redis，但镜像内没有 Docker CLI；仅挂载 `/var/run/docker.sock` 仍无法执行 maker/mineru 转换容器。
- MSE 主机资源紧张：约 1.7 GiB 内存，重建 MinerU 转换镜像时 SSH banner 与后端 `/health` 均出现超时。

代码修复：

- `5054ff3 fix: restore production mse worker conversion`
  - 生产 strict 模式下，API 入队失败不再 inline 处理 PDF，而是返回 `503 queue unavailable`，避免上传请求长时间占用 API 进程。
  - worker `arq` job timeout 提升到 `WORKER_JOB_TIMEOUT_SECONDS=2400`。
- `04322bf fix: stabilize production deploy worker docker access`
  - worker 挂载 `/var/run/docker.sock` 与宿主机 `/usr/bin/docker`，让 Docker 转换逻辑在 worker 容器内可执行。
  - 生产部署脚本默认禁用 BuildKit，避免该机器上 buildx 构建转换镜像卡死。
- `78b06ab fix: allow skipping converter rebuilds during deploy`
  - 部署脚本新增 `SKIP_CONVERTER_BUILD=1`，已有 maker/mineru 镜像时可只重建 API/worker。

本地回归：

```text
PYTHONPATH=packages:apps python3 -m pytest \
  tests/test_mse_converter_strict.py \
  tests/test_mse_final_live_script.py \
  tests/test_mse_quasi_prod_script.py \
  tests/test_mse_core_loop.py -q

15 passed
```

生产部署状态：

- `mse-tyrion` 已推送至 `78b06ab`。
- 2026-06-08 22:05 左右手动部署先执行转换镜像重建；maker 镜像构建完成，MinerU 镜像构建期间主机负载升高，公网 `/health` 与 SSH 登录均超时。
- 已终止本地部署 SSH 会话；远端 `git rev-parse --short HEAD` 一度确认到 `04322bf`，且未发现残留 `docker build` 进程。
- 截至 2026-06-08 22:30，SSH 仍在 banner 阶段超时，`https://api-mse.tyrion.space/health` 仍超时；尚未能执行 `SKIP_CONVERTER_BUILD=1` 的轻量部署，因此公网复测未完成。

## 生产体验复测（2026-06-09）

执行时间：2026-06-09 21:13-21:22 CST。

目标：继续以真实用户视角体验公网平台，并确认是否达到生产预期。

### 初始状态

- `GET https://api-mse.tyrion.space/health` 返回 `HTTP 200`，`time_total=2.404017`。
- `ssh mse` 恢复可用，远端负载约 `load average: 5.97, 3.76, 3.17`。
- 远端 `/opt/fudan-pager-check-mse` 仍停留在 `04322bf`，未包含 `78b06ab` / `6c82948` 的部署脚本与验收文档更新。

### 尝试部署最新修复

执行：

```bash
cd /opt/fudan-pager-check-mse
git fetch --prune origin +refs/heads/mse-tyrion:refs/remotes/origin/mse-tyrion
git checkout -B mse-tyrion origin/mse-tyrion
SKIP_CONVERTER_BUILD=1 DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 \
  DEPLOY_BRANCH=mse-tyrion ./deploy/git-pull-deploy.sh
```

结果：

- 远端代码切到 `6c82948`。
- 部署脚本确认输出 `skip converter image build`，未重建 maker/mineru 转换镜像。
- 随后进入 API/worker 应用镜像 build 的 `pip install` 阶段，公网 `/health` 开始超时，SSH 再次出现 `Connection timed out during banner exchange`。
- 为避免继续压垮后端，已终止本地 SSH 部署会话。
- 等待约 1 分钟后，`GET https://api-mse.tyrion.space/health` 仍 `HTTP=000`、20 秒超时；`ssh mse` 仍在 banner 阶段超时。

### 前端体验

前端由 Vercel 承载，静态路由可访问：

| 路由 | 结果 |
|------|------|
| `/` | `HTTP 307`，约 0.84s，跳转 dashboard |
| `/login` | `HTTP 200`，约 0.61s |
| `/register` | `HTTP 200`，约 0.79s |
| `/dashboard` | `HTTP 200`，约 0.68s |
| `/mse/dashboard` | `HTTP 200`，约 0.83s |
| `/mse/projects/new` | `HTTP 200`，约 0.81s |
| `/mse/invite/test-token` | `HTTP 200`，约 2.06s |

### 体验结论

本次生产体验仍未通过。

前端页面可打开，但后端 API 在应用镜像构建压力下持续超时，SSH 也会失去可用性。用户实际体验会表现为登录、注册、项目创建、邀请接受、PDF 上传和报告查询均无法稳定完成。因此当前平台没有达到生产预期。

当前最高优先级不是继续补业务功能，而是修生产运行方式：

- 不应在 1.7 GiB 内存的生产机器上现场 `docker compose up --build`。
- API/worker 镜像应在 CI 或更大构建机预构建后推送，生产机器只执行 `docker compose pull && docker compose up -d`。
- 后端运行机需要扩容或迁移；当前容量无法同时承载 API、worker、Redis、Docker 转换和构建任务。
- 自动部署 timer 已在部署尝试前停止；恢复前应先改成“不在生产机 build”的发布方式。

## 预构建发布修复记录（2026-06-09）

执行时间：2026-06-09 21:24-21:48 CST。

已完成：

- `e2150f6 fix: deploy mse backend from prebuilt image`
  - 生产 compose 的 `api` / `worker` 改为 `image: ${APP_IMAGE}`，移除 `build:`。
  - `deploy/git-pull-deploy.sh` 改为 `docker compose up -d --no-build`。
  - 部署前校验 `APP_IMAGE`、`MAKER_IMAGE`、`MINERU_IMAGE` 已加载；缺失直接失败。
  - 增加磁盘/内存 preflight 与健康检查失败后回滚上一版 `APP_IMAGE`。
  - 新增 `deploy/release-prebuilt-app.sh`：本地/构建机 build `linux/amd64` 应用镜像、`docker save | gzip`、`scp`、远端 `docker load`、写入 `APP_IMAGE`、无构建部署。
  - 新增 `deploy/build-converter-images.sh`：转换镜像独立构建，常规部署不再构建 maker/mineru。
  - 自动部署 timer 默认安装后保持禁用，需 `ENABLE_AUTO_DEPLOY=1` 显式启用。
- `bd0f853 fix: allow mirrored python base for prebuilt image`
  - 应用 Dockerfile 支持 `PYTHON_IMAGE` build arg，Docker Hub 不稳定时可使用兼容镜像源。
  - 本次使用 `public.ecr.aws/docker/library/python:3.12-slim` 成功构建本地 `linux/amd64` 应用镜像。

本地验证：

```text
bash -n deploy/git-pull-deploy.sh deploy/deploy.sh deploy/install-auto-deploy.sh \
  deploy/release-prebuilt-app.sh deploy/build-converter-images.sh && git diff --check

PYTHONPATH=packages:apps python3 -m pytest \
  tests/test_deploy_prebuilt_release.py \
  tests/test_mse_converter_strict.py \
  tests/test_mse_core_loop.py \
  tests/test_mse_quasi_prod_script.py -q

npm run lint && npm run build
```

结果：

- shell 语法与 `git diff --check` 通过。
- pytest `16 passed`。
- 前端 lint 与 Next production build 通过。
- 本地镜像 `fudan-pager-mse-app:d850c8d80be3` 已构建成功，架构为 `amd64 linux`。
- 镜像压缩包已生成：`/tmp/fudan-pager-mse-app_d850c8d80be3.tar.gz`，大小约 211 MB。

生产发布状态：

- 应用镜像对应的代码提交为 `d850c8d`；本小节后续文档提交不影响应用镜像内容。
- 截至 2026-06-09 21:48，`ssh mse` 仍在 banner 阶段超时，`GET https://api-mse.tyrion.space/health` 仍 15 秒超时。
- 因生产入口不可控，尚未能执行 `scp`、远端 `docker load`、无构建部署和公网业务复测。

## 后续复测建议

修复 worker/Redis/inline fallback 问题后，按以下顺序复测：

1. `curl https://api-mse.tyrion.space/health`
2. 注册测试导师/学生。
3. 创建 MSE 项目并确认默认规则索引。
4. 生成邀请并绑定学生。
5. 上传真实 PDF，确认提交接口快速返回 `round_number` / `job_id`。
6. 轮询报告直到 `pending_release`、`issues_found` 或 `passed`，不得出现 `parse_failed` / `analysis_failed`。
7. 导出 `.md` / `.pdf`。
8. 使用 CNKI/机构硕士论文与学校规范补跑 M1-5 私有样本验收。
