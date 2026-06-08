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
