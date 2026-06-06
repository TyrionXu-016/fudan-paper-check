# MSE 测试样例目录

本目录用于存放**不提交仓库**的知网硕士论文 PDF 与学院规范文档。

## 结构

- `manifest.yaml` — 测试集清单（tier、学科、是否 primary）
- `theses/*.pdf` — 本地 PDF（已 gitignore）
- `converted/` — 转换后的 maker/mineru MD
- `specs/` — 各校撰写规范（供 RAG 测试）
- `golden/` — Issue / 门禁期望快照

## 快速验收（无 PDF）

CI 与本地无 PDF 时，使用仓库根目录 `samples/*_maker.md` 作为 fallback。

```bash
./scripts/mse_acceptance.sh
```

## 添加 Tier A 论文

1. 从 CNKI 或机构库下载 CS 硕士 PDF，并准备对应学院规范（PDF 或 Markdown）
2. 用导入脚本校验并复制到本目录，同时更新 `manifest.yaml`：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_import_private_sample.py \
  --pdf ~/Downloads/cnki-thesis.pdf \
  --spec ~/Downloads/school-spec.pdf \
  --school "Example University" \
  --subfield software_engineering
```

3. 检查本地样本是否齐备：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_check_sample_manifest.py --require-primary
```

4. 运行 `PDF_CONVERTER_MODE=docker` 转换后写入 `converted/`

API 已按本地准生产环境启动后，运行 M1-5 live 验收：

```bash
PYTHONPATH=packages:apps python3 scripts/mse_acceptance_private_samples.py
```
