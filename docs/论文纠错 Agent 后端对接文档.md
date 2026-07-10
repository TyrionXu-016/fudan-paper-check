# 论文纠错 Agent 后端对接文档

本文档用于对齐 `apps/web-vue` 前端与后端 API 的接入契约。当前 Vue 前端实际调用的是 `/v1/*` 接口，默认开发模式走 mock；接真实后端时需要在 `apps/web-vue/.env.local` 配置。

更新时间：2026-07-08

```env
VITE_USE_MOCK=false
VITE_API_BASE=http://localhost:8000
```

## 1. 接入总览

### 1.1 前端调用入口

前端接口代码位于：

- `fudan-pager-check/apps/web-vue/src/api/checkApi.ts`
- `fudan-pager-check/apps/web-vue/src/api/authApi.ts`
- `fudan-pager-check/apps/web-vue/src/api/chunk.ts`
- `fudan-pager-check/apps/web-vue/src/api/sse.ts`
- `fudan-pager-check/apps/web-vue/src/api/decisionApi.ts`
- `fudan-pager-check/apps/web-vue/src/api/exportApi.ts`
- `fudan-pager-check/apps/web-vue/src/api/previewApi.ts`
- `fudan-pager-check/apps/web-vue/src/api/adapter.ts`
- `fudan-pager-check/apps/web-vue/src/api/docAdapter.ts`

### 1.2 当前主流程

1. 前端登录或注册，保存 JWT 到 `localStorage.fpc_token`。
2. 前端请求 `GET /v1/rule_bases` 获取规范列表。
3. 用户上传论文，前端调用 `POST /v1/check`，大文件会优先尝试分片上传。
4. 后端返回 `task_id`。
5. 前端通过 SSE 或轮询获取任务进度。
6. 任务完成后，前端请求 `GET /v1/result/{task_id}` 获取问题列表。
7. 前端请求 `GET /v1/result/{task_id}/document` 获取结构化论文预览数据。
8. 用户接受、拒绝、自定义修改问题时，前端会本地更新预览，并在真实后端模式下自动同步单条 decision。
9. 导出时，普通问题决策优先走后端导出；如果用户进入过“整篇手动编辑”并产生自由编辑内容，则前端走本地导出，避免后端丢失整篇 HTML 编辑结果。

### 1.3 当前实现状态

| 能力 | 前端状态 | 后端状态 | 说明 |
| --- | --- | --- | --- |
| 普通上传检测 | 已接入 | 已有 `/v1/check` | 小文件直接 multipart 上传 |
| 分片上传 | 已接入 | 已补 `/v1/check/chunks/*` | 默认 `>=10MB` 走分片，完成后返回 `task_id` |
| SSE 进度 | 已接入 | 已支持双路径 | 前端当前连 `/v1/detect/progress/{task_id}?token=...` |
| 轮询进度 | 已接入 | 已有 `/v1/tasks/{task_id}` | SSE 失败后降级轮询 |
| 切换规范重检 | 已接入 | 已有 `/v1/tasks/{task_id}/restart` | 优先复用后端原始上传文件 |
| 结果报告 | 已接入 | 已有 `/v1/result/{task_id}` | 用于问题列表 |
| 结构化文档 | 已接入 | 已有 `/v1/result/{task_id}/document` | 用于右侧论文预览 |
| 单条决策同步 | 已接入 | 已有 PATCH decision | 接受/拒绝/自定义/撤销均会同步 |
| 后端 preview | 已封装 | 已有 `/v1/tasks/{task_id}/preview` | 当前主要用于导出后校验，右侧主预览仍以前端本地渲染为主 |
| 后端导出 | 已接入 | 已有 `/v1/tasks/{task_id}/export` | 普通决策导出走后端；整篇手动编辑后走本地导出 |

## 2. 通用约定

### 2.1 Base URL

默认后端地址：

```text
http://localhost:8000
```

生产环境通过 `VITE_API_BASE` 指向真实 API 域名。

### 2.2 鉴权

除登录、注册、规范列表等公开接口外，任务相关接口建议要求 JWT。

前端会自动在 Axios 请求头中注入：

```http
Authorization: Bearer <access_token>
```

SSE 的 `EventSource` 不能直接设置请求头，前端当前会把 token 放到查询参数：

```text
?token=<access_token>
```

当前后端 SSE 已支持该 query token；未传 query token 时仍可使用 Bearer header。

### 2.3 统一响应包裹

前端响应拦截器支持两种返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

或直接返回业务对象。建议后端统一使用第一种。

错误响应建议：

```json
{
  "code": "TASK_NOT_READY",
  "message": "result not ready",
  "data": null,
  "detail": "optional detail"
}
```

前端遇到 HTTP 401 会清空本地 token 并触发重新登录。

### 2.4 常用错误码

| code | HTTP | 说明 |
| --- | ---: | --- |
| `UNAUTHORIZED` | 401 | 未登录或 token 失效 |
| `FILE_TOO_LARGE` | 413 | 文件过大 |
| `UNSUPPORTED_FORMAT` | 400 | 文件或导出格式不支持 |
| `RULE_BASE_NOT_FOUND` | 404 | 规范不存在 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `TASK_NOT_READY` | 409 | 任务未完成，结果暂不可用 |
| `TASK_BUSY` | 409 | 任务处理中，不允许重启或覆盖 |
| `DETECT_FAILED` | 500 | 检测失败 |
| `INVALID_CHUNK` | 400 | 分片序号或总数非法 |
| `MISSING_CHUNK` | 400 | 分片完成时存在缺片 |
| `INVALID_CHUNK_UPLOAD` | 400 | 分片上传完成请求非法或组装大小不一致 |
| `FORBIDDEN` | 403 | 当前用户无权访问该任务或分片上传 |

## 3. 认证接口

### 3.1 注册

```http
POST /v1/auth/register
Content-Type: application/json
```

请求体：

```json
{
  "email": "student@example.com",
  "password": "123456",
  "name": "张三"
}
```

响应 `data`：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "u_001",
    "email": "student@example.com",
    "name": "张三",
    "role": "student"
  }
}
```

### 3.2 登录

```http
POST /v1/auth/login
Content-Type: application/json
```

请求体：

```json
{
  "email": "student@example.com",
  "password": "123456"
}
```

响应同注册。

### 3.3 当前用户

```http
GET /v1/auth/me
Authorization: Bearer <token>
```

响应 `data`：

```json
{
  "id": "u_001",
  "email": "student@example.com",
  "name": "张三",
  "role": "student"
}
```

## 4. 规范接口

### 4.1 规范列表

```http
GET /v1/rule_bases
```

响应 `data`：

```json
[
  {
    "id": "fudan_university",
    "display_name": "复旦大学本科论文规范",
    "summary": {
      "format": ["标题层级规范", "页边距与行距要求"],
      "reference": ["参考文献格式", "引用编号一致性"],
      "typo": ["错别字检查"],
      "grammar": ["语病检查"],
      "polish": ["学术化润色"],
      "logic": ["段落逻辑与论证连贯性"]
    }
  }
]
```

前端会映射为：

```ts
{
  id: string
  name: display_name
  short: display_name
  version: ''
  summary: Record<string, string[]>
}
```

### 4.2 规范详情

当前 Vue 前端不强依赖该接口，但后端已有接口可保留：

```http
GET /v1/rule_bases/{rule_base_id}
```

## 5. 上传与检测

### 5.1 普通上传

```http
POST /v1/check
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `file` | File | 是 | 论文文件，建议支持 `.pdf`、`.docx`、`.md` |
| `rule_base_id` | string | 是 | 规范 ID |

响应 `data`：

```json
{
  "task_id": "task_20260708_001",
  "status": "queued"
}
```

前端只强依赖 `task_id`。

### 5.2 分片上传

当前 Vue 前端对大于等于 `VITE_CHUNK_UPLOAD_THRESHOLD` 的文件会先尝试分片上传，默认阈值为 10MB，默认分片大小为 2MB。

后端已补齐 `/v1/check/chunks/*` 路由。前端仍保留兼容策略：如果分片上传失败，会回退到普通 `POST /v1/check`。

#### 初始化

```http
POST /v1/check/chunks/init
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "filename": "paper.pdf",
  "size": 20971520,
  "chunks": 10,
  "rule_base_id": "fudan_university"
}
```

响应 `data`：

```json
{
  "upload_id": "upload_001"
}
```

#### 上传单片

```http
POST /v1/check/chunks/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `upload_id` | string | 初始化返回的上传 ID |
| `index` | string | 从 0 开始的分片序号 |
| `total` | string | 总分片数 |
| `chunk` | File | 当前分片 |

响应 `data` 可为空对象：

```json
{}
```

#### 完成上传

```http
POST /v1/check/chunks/complete
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "upload_id": "upload_001"
}
```

响应 `data`：

```json
{
  "task_id": "task_20260708_001",
  "status": "queued"
}
```

后端处理要求：

- `init` 阶段校验 `rule_base_id`、文件总大小和用户身份，返回 `upload_id`。
- `upload` 阶段校验 `upload_id` 归属、`index` 范围和 `total` 一致性。
- `complete` 阶段校验是否缺片、组装后大小是否等于初始化 size，并创建检测任务。
- 组装成功后应清理临时分片目录。

### 5.3 切换规范后重检

真实后端模式下，用户已完成一次检测后切换规范，前端优先调用后端 restart，而不是重新上传浏览器里的文件。

```http
POST /v1/tasks/{task_id}/restart
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `rule_base_id` | string | 是 | 新规范 ID |

响应 `data`：

```json
{
  "task_id": "task_20260708_001",
  "status": "queued"
}
```

前端行为：

- 有 `currentTaskId` 时调用 `restart`，后端复用原始上传文件。
- 无 `currentTaskId` 但浏览器仍持有 `File` 时，回退到重新上传。
- 重检会清空当前 issues、decisions、version history、editor 状态。

## 6. 任务进度

### 6.1 轮询任务状态

```http
GET /v1/tasks/{task_id}
Authorization: Bearer <token>
```

响应 `data`：

```json
{
  "task_id": "task_20260708_001",
  "status": "checking",
  "rule_base_id": "fudan_university",
  "filename": "paper.pdf",
  "error": null,
  "current_stage": "FORMAT_CHECK",
  "progress_percent": 35,
  "progress_message": "正在检查格式规范",
  "created_at": "2026-07-08T10:00:00Z",
  "updated_at": "2026-07-08T10:00:20Z"
}
```

前端状态映射：

| 后端 `status` | 前端状态 |
| --- | --- |
| `queued` / `converting` / `parsing` / `checking` | `DETECTING` |
| `done` | `DONE` |
| `failed` | `ERROR` |

### 6.2 检测阶段枚举

建议使用：

```text
UPLOADING
PARSING
FORMAT_CHECK
TYPO_CHECK
GRAMMAR_CHECK
POLISH
LOGIC_CHECK
REFERENCE_CHECK
DONE
ERROR
```

### 6.3 SSE 进度

前端当前代码订阅：

```http
GET /v1/detect/progress/{task_id}?token=<token>
Accept: text/event-stream
```

后端同时支持别名：

```http
GET /v1/tasks/{task_id}/progress?token=<token>
Accept: text/event-stream
```

说明：

- `EventSource` 无法设置 `Authorization` header，前端通过 query 参数传 `token`。
- 后端 SSE 鉴权需要优先支持 `?token=`，未传 token 时仍可回退到 Bearer header。
- 前端监听 `progress`、`done`、`error` 三类事件。

SSE 事件格式：

```text
event: progress
data: {"status":"DETECTING","stage":"FORMAT_CHECK","percent":35,"message":"正在检查格式规范","issueCount":0}

event: done
data: {"status":"DONE","stage":"DONE","percent":100,"message":"检测完成","issueCount":17}

event: error
data: {"status":"ERROR","stage":"ERROR","percent":0,"message":"检测失败"}
```

前端会监听 `progress`、`done`、`error` 三类事件。SSE 重连超过 `VITE_MAX_PROGRESS_RETRIES` 后，会自动降级为 `GET /v1/tasks/{task_id}` 轮询。

## 7. 检测结果

### 7.1 获取检查报告

```http
GET /v1/result/{task_id}
Authorization: Bearer <token>
```

如果任务未完成，返回 HTTP 409 + `TASK_NOT_READY`。完成后响应 `data`：

```json
{
  "job_id": "task_20260708_001",
  "paper_title": "论文标题",
  "summary": {
    "errors": 2,
    "warnings": 12,
    "infos": 3
  },
  "issues": [
    {
      "id": "issue_001",
      "issue_type": "typo",
      "original_text": "以经完成实验",
      "suggested_text": "已经完成实验",
      "span_id": "span_001",
      "code": "TYPO_COMMON",
      "category": "format",
      "severity": "warning",
      "section": "abstract",
      "line": 12,
      "page": 1,
      "page_line": "第 1 页第 12 行",
      "rule_ref": "错别字检查",
      "revision_hint": "将“以经”改为“已经”",
      "message": "疑似错别字",
      "suggestion": "建议替换为“已经完成实验”",
      "evidence": "上下文..."
    }
  ]
}
```

### 7.2 Issue 字段要求

| 字段 | 类型 | 必填 | 前端用途 |
| --- | --- | --- | --- |
| `id` | string | 是 | 问题唯一 ID |
| `issue_type` | string | 否 | 映射前端问题分类 |
| `original_text` | string | 是 | 修改前文本 |
| `suggested_text` | string | 是 | 修改后文本 |
| `span_id` | string \| null | 否 | 绑定预览区高亮；为空时按全文级问题展示 |
| `code` | string | 是 | 规则码，展示为解释信息 |
| `category` | string | 是 | 兜底分类 |
| `severity` | string | 是 | `error` / `warning` / `info` |
| `section` | string | 否 | 位置展示 |
| `line` | number | 否 | 行号 |
| `page` | number | 否 | 页码 |
| `page_line` | string | 否 | 优先展示的页行位置 |
| `message` | string | 否 | 后端问题说明 |
| `suggestion` | string | 否 | 后端修改建议 |

### 7.3 问题类型映射

| 后端 `issue_type` | 前端分类 |
| --- | --- |
| `format` | `FORMAT` |
| `reference` | `FORMAT` |
| `typo` | `TYPO` |
| `grammar` | `GRAMMAR` |
| `polish` | `POLISH` |
| `llm` | `POLISH` |
| `logic_contradiction` | `LOGIC` |
| `paragraph_logic` | `PARA_LOGIC` |
| `sentence_split` | `SPLIT` |

如果 `issue_type` 为空，前端会根据 `category` 兜底映射；仍无法识别时归为 `FORMAT`。

## 8. 文档预览结构

### 8.1 获取结构化文档

```http
GET /v1/result/{task_id}/document
Authorization: Bearer <token>
```

响应 `data`：

```json
{
  "paper_title": "论文标题",
  "sections": [
    {
      "id": "sec_abstract",
      "kind": "abstract",
      "title": "摘要",
      "level": 1,
      "start_line": 1,
      "end_line": 8,
      "parent_id": null
    }
  ],
  "spans": [
    {
      "id": "span_001",
      "section_id": "sec_abstract",
      "block_id": "block_001",
      "start_offset": 0,
      "end_offset": 8,
      "text": "以经完成实验",
      "line_start": 2,
      "line_end": 2,
      "page": 1
    }
  ]
}
```

前端会按 `section_id` 分组、按 `start_offset` 排序、按 `block_id` 合并段落。若某个 issue 的 `span_id` 命中 span，则该 span 会变成可交互高亮节点。

## 9. 决策、预览与导出

当前 Vue 前端已经接入后端 decisions、preview、export。需要注意导出有双轨：

- 普通问题级决策：优先走后端导出。
- 用户进入过“整篇手动编辑”并产生自由编辑内容：走前端本地导出，确保当前预览内容不丢失。

### 9.1 保存决策

```http
PUT /v1/tasks/{task_id}/decisions
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "decisions": [
    {
      "issue_id": "issue_001",
      "action": "accept",
      "custom_content": null
    },
    {
      "issue_id": "issue_002",
      "action": "custom",
      "custom_content": "用户自定义修改内容"
    }
  ]
}
```

`action` 枚举：

```text
pending
accept
reject
custom
```

### 9.2 单条决策更新

```http
PATCH /v1/tasks/{task_id}/decisions/{issue_id}
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "issue_id": "issue_001",
  "action": "reject",
  "custom_content": null
}
```

前端触发时机：

- 点击接受：`action = accept`
- 点击拒绝：`action = reject`
- 自定义修改：`action = custom`，`custom_content` 为用户文本或含行内格式的 HTML
- 撤销单条或全局撤销回到未处理：`action = pending`

同步策略：

- 前端本地预览会先更新，再异步 PATCH 后端。
- PATCH 失败不会回滚本地预览，只弹出“决策同步失败”提示。
- 批量接受/拒绝会逐条 PATCH。

### 9.3 获取后端预览

```http
GET /v1/tasks/{task_id}/preview
Authorization: Bearer <token>
```

响应 `data`：

```json
{
  "task_id": "task_20260708_001",
  "paper_title": "论文标题",
  "spans": [
    {
      "span_id": "span_001",
      "section_id": "sec_abstract",
      "text": "已经完成实验",
      "highlight": "ai"
    }
  ],
  "unresolved_count": 3
}
```

当前前端用途：

- 前端已封装 `getBackendPreview(taskId)`。
- 右侧主预览仍以前端本地 `document + decisions + version history` 渲染为主，以保证交互即时性。
- 后端 preview 当前主要用于导出后非阻塞校验 `unresolved_count`。

### 9.4 创建导出文件

```http
POST /v1/tasks/{task_id}/export
Authorization: Bearer <token>
Content-Type: application/json
```

请求体：

```json
{
  "format": "docx",
  "decisions": [
    {
      "issue_id": "issue_001",
      "action": "accept",
      "custom_content": null
    }
  ]
}
```

`format` 支持：

```text
docx
pdf
md
```

响应 `data`：

```json
{
  "unresolved_count": 0,
  "filename": "task_20260708_001.docx",
  "format": "docx"
}
```

### 9.5 下载导出文件

```http
GET /v1/tasks/{task_id}/export/{fmt}
Authorization: Bearer <token>
```

`fmt` 支持：

```text
docx
md
pdf
```

响应为文件流。

前端导出策略：

- 若 `VITE_USE_MOCK=false`、存在 `task_id`、且整篇编辑器未产生自由编辑内容，则：
  1. `POST /v1/tasks/{task_id}/export`
  2. `GET /v1/tasks/{task_id}/export/{fmt}`
  3. 浏览器下载文件
- 若用户使用过整篇手动编辑，则前端直接本地导出 Word/PDF，避免后端不了解自由编辑 HTML 导致内容丢失。

## 10. 整篇手动编辑与 span 同步

这是前端内部能力，但会影响后端 decision / export 对接理解。

### 10.1 span 级编辑同步

前端进入“手动编辑”模式时，会把文档构造成带标识的 HTML：

```html
<span data-span-id="span_001" data-issue-id="issue_001">原文内容</span>
```

用户切回预览模式时，前端会扫描所有 `data-span-id` 节点：

1. 对比该节点当前 HTML 与 `version.current(spanId)`。
2. 若发生变化，调用 `issues.applyManualEdit(spanId, html)`。
3. 若该 span 绑定了 issue，则该 issue 变为 `custom` 决策。
4. 预览区对应位置显示蓝色高亮。
5. 修改记录进入 span 版本历史。
6. 真实后端模式下，同步 PATCH decision，`custom_content` 可能包含行内 HTML。

### 10.2 边界说明

如果用户在整篇编辑器中删除了整个 `data-span-id` 外壳、合并/拆分段落或大幅移动结构，前端无法可靠映射回原始 span。这类结构性大改：

- 会保留在前端本地编辑 HTML 中。
- 本地导出可以保留内容。
- 不会转换成 span 级蓝色高亮和后端 decision。

## 11. CORS 与本地联调

前端 Vite 默认地址通常为：

```text
http://localhost:5173
```

后端 CORS 需要允许：

```text
http://localhost:5173
http://127.0.0.1:5173
```

当前后端默认 CORS 已包含：

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

如果还保留 Next.js 旧前端，也可继续允许：

```text
http://localhost:3000
http://127.0.0.1:3000
```

## 12. 当前差异与建议

| 项目 | Vue 前端现状 | 后端现状 | 建议 |
| --- | --- | --- | --- |
| SSE 路径 | `/v1/detect/progress/{id}` | 已支持 `/v1/detect/progress/{id}` 和 `/v1/tasks/{id}/progress` | 保持双路径兼容 |
| SSE 鉴权 | query 参数 `token` | 已支持 query token，未传时支持 Bearer header | 保持现状 |
| 分片上传 | `>=10MB` 优先走 `/v1/check/chunks/*` | 已补路由 | 仍需真实大文件验收 |
| 切换规范重检 | 优先调用 `/v1/tasks/{id}/restart` | 已有 restart | 需确认 active task 时返回 `TASK_BUSY` |
| 决策同步 | 本地先更新，再 PATCH 后端 | 已有 PATCH decision | 后端应允许 `pending` 撤销状态 |
| 导出 | 普通决策走后端；整篇自由编辑走本地 | 后端已有导出接口 | 若要统一后端导出，需要新增整篇 HTML 提交接口 |
| 响应包裹 | 支持 `data` 解包 | 后端已有 `ApiResponse` | 保持统一 |

## 13. 最小验收清单

以下接口为 Vue 前端主链路依赖：

- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `GET /v1/auth/me`
- `GET /v1/rule_bases`
- `POST /v1/check`
- `GET /v1/tasks/{task_id}`
- `GET /v1/result/{task_id}`
- `GET /v1/result/{task_id}/document`

以下接口为当前增强链路依赖：

- `GET /v1/tasks/{task_id}/progress`
- `GET /v1/detect/progress/{task_id}`
- `PUT /v1/tasks/{task_id}/decisions`
- `PATCH /v1/tasks/{task_id}/decisions/{issue_id}`
- `GET /v1/tasks/{task_id}/preview`
- `POST /v1/tasks/{task_id}/restart`
- `POST /v1/check/chunks/init`
- `POST /v1/check/chunks/upload`
- `POST /v1/check/chunks/complete`
- `POST /v1/tasks/{task_id}/export`
- `GET /v1/tasks/{task_id}/export/{fmt}`

完成后前端联调步骤：

1. 在 `apps/web-vue/.env.local` 写入 `VITE_USE_MOCK=false` 和 `VITE_API_BASE`。
2. 启动后端 API。
3. 启动 Vue 前端。
4. 注册或登录。
5. 上传 `.pdf` 或 `.docx`。
6. 确认进度条更新、问题列表出现、右侧预览区能正确高亮。
7. 点击接受、拒绝、自定义修改，确认预览区实时更新。
8. 点击接受、拒绝、自定义修改，确认后端 decisions 接口收到 PATCH。
9. 切换规范，确认调用 `/v1/tasks/{task_id}/restart` 并重新进入检测。
10. 上传大于 10MB 的文件，确认走分片接口并能完成检测。
11. 导出 Word/PDF，确认普通决策走后端下载。
12. 进入整篇手动编辑，修改某个高亮 span 后切回预览，确认蓝色高亮和历史记录出现。
13. 整篇手动编辑后导出，确认走前端本地导出且内容不丢失。
