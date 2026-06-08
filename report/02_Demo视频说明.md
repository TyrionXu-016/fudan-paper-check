# Demo 视频说明

视频文件建议命名为 `04_demo_video.mp4`，与本说明文档放在同一提交目录下。若评审提交系统只允许提交仓库链接，可将视频上传到仓库 Release、网盘或课堂系统，并在提交说明中补充访问链接。

## 一、建议录制流程

| 顺序 | 建议画面 | 说明 |
|---|---|---|
| 1 | 展示仓库目录和 README | 说明项目为论文纠错智能 Agent，核心目录包括 `apps/`、`packages/`、`config/`、`tests/` |
| 2 | 启动后端 API | 执行 `python3 -m uvicorn api.main:app --reload --app-dir apps`，展示 `/health` 返回正常 |
| 3 | 启动前端 | 进入 `apps/web-next` 执行 `npm run dev`，浏览器打开 `http://localhost:3000` |
| 4 | 注册/登录 | 使用 Demo 账号登录系统，进入任务或上传页面 |
| 5 | 上传论文 | 上传样例 Markdown 或 PDF 文件，并选择规范库 |
| 6 | 展示 Agent 执行过程 | 展示任务状态、SSE 进度阶段、解析/检查/完成状态 |
| 7 | 展示检查报告 | 查看 Issue 列表、严重程度、证据、建议和章节定位 |
| 8 | 展示决策与导出 | 对若干 Issue 做接受/拒绝/自定义修改，生成预览并导出 docx/pdf |
| 9 | 说明限制 | 说明 PDF 解析质量、LLM API Key、规范库覆盖范围等当前限制 |

## 二、推荐 Demo 命令

### 后端 API

```bash
python3 -m pip install pydantic pyyaml httpx fastapi "uvicorn[standard]" python-multipart arq redis eval_type_backport pyjwt python-docx reportlab docker pytest
export PYTHONPATH=packages:apps
python3 -m uvicorn api.main:app --reload --app-dir apps
```

默认地址：`http://localhost:8000`

### Next.js 前端

```bash
cd apps/web-next
cp .env.local.example .env.local
npm install
npm run dev
```

默认地址：`http://localhost:3000`

### 可选 Docker Compose

```bash
docker compose up --build
```

## 三、关键结果说明

| 结果 | 证据位置 | 说明 |
|---|---|---|
| 后端启动成功 | 视频中展示 `/health` 或终端日志 | FastAPI 服务正常运行 |
| 前端启动成功 | 视频中展示 `http://localhost:3000` | 可进入登录、上传、任务和报告页面 |
| 论文任务创建成功 | 视频中展示任务 ID 或任务列表 | 上传后生成异步检测任务 |
| 进度可观察 | 视频中展示检测进度或阶段状态 | 系统包含解析、格式检查、语法检查、润色、逻辑检查、参考文献检查等阶段 |
| 报告生成成功 | 视频中展示 Issue 列表或 Markdown 报告 | 报告包含错误、警告、提示统计和问题证据 |
| 修改决策可用 | 视频中展示接受/拒绝/自定义修改 | 决策会影响预览和导出结果 |
| 导出可用 | 视频中展示 docx/pdf 下载或生成结果 | 支持将修改结果导出为文档 |

仓库已有 `local_test_report.md` 可作为静态结果证据。该报告记录了一次样例论文检查：系统识别到 DOI 格式、OCR 数值空格、格式规范等问题，并输出错误、警告和提示统计。

## 四、视频中可讲解的核心亮点

1. 系统不是单一文本校对工具，而是论文解析、规范库、RAG、Agent、报告和导出的完整流程。
2. 规范检查采用规则引擎和 RAG-1 规则切片结合：规则负责判定，RAG 负责提供规范依据。
3. 内容纠错、逻辑检查和润色可通过 RAG-2 获取当前论文 span 上下文，减少整篇论文直接塞入 Prompt 的成本。
4. 系统保留规则模式、Agent 模式和 hybrid 模式，便于无 API Key 环境下演示基础能力。
5. 后端 API、前端界面、Worker、测试、部署材料都已在仓库内组织。

## 五、已知限制

1. 如果未配置 LLM API Key，语义纠错和润色效果会低于完整 Agent 模式。
2. PDF 转换依赖 Maker/MinerU 兼容镜像，扫描版或低质量 PDF 解析效果不稳定。
3. 当前规范库覆盖范围有限，更多学校和期刊规则需要后续扩展。
4. Word/PDF 导出当前优先保证文本和决策正确，复杂排版仍需人工复核。
5. 成员年级、专业等信息需在最终提交前由项目组补齐。
