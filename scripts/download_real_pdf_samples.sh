#!/usr/bin/env bash
# 下载开放获取论文 PDF，供 MinerU / MSE 真实解析测试（arXiv，CC BY 4.0）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/samples/real_pdfs"
mkdir -p "$OUT"

download() {
  local url="$1"
  local out="$2"
  if [[ -f "$out" && -s "$out" ]]; then
    echo "skip (exists): $out"
    return
  fi
  echo "download: $out"
  curl -fsSL --retry 3 --max-time 180 -o "$out" "$url"
}

download "https://arxiv.org/pdf/1706.03762.pdf" "$OUT/arxiv_attention_is_all_you_need.pdf"
download "https://arxiv.org/pdf/2106.09685.pdf" "$OUT/arxiv_lora_efficient_finetuning.pdf"
download "https://arxiv.org/pdf/2401.02954.pdf" "$OUT/arxiv_deepseek_llm.pdf"

echo "done: $(ls -lh "$OUT"/*.pdf)"
