# 真实论文 PDF 样例（开放获取）

用于 `PDF_CONVERTER_MODE=docker` 下的 MinerU/Maker 解析与 MSE 提交流程测试。

| 文件 | 来源 | 许可 |
|------|------|------|
| `arxiv_attention_is_all_you_need.pdf` | [arXiv:1706.03762](https://arxiv.org/abs/1706.03762) | CC BY 4.0 |
| `arxiv_lora_efficient_finetuning.pdf` | [arXiv:2106.09685](https://arxiv.org/abs/2106.09685) | CC BY 4.0 |
| `arxiv_deepseek_llm.pdf` | [arXiv:2401.02954](https://arxiv.org/abs/2401.02954) | CC BY 4.0 |

重新下载：

```bash
./scripts/download_real_pdf_samples.sh
```

默认验收 PDF（`.env` 中 `MINERU_TEST_PDF`）建议指向体积较小的 `arxiv_attention_is_all_you_need.pdf`。

**说明**：仓库内 `fudan-pager-mineru` 镜像为 Docker 占位实现；若需官方 MinerU 版式解析，请将 `MINERU_IMAGE` 换为自建的真实 MinerU 镜像。
