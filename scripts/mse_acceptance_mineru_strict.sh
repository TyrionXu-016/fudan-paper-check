#!/usr/bin/env bash
# 阶段 5：MinerU 严格模式验收
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${API_BASE:-http://127.0.0.1:8000}"

echo "=== MinerU 严格模式单元测试 ==="
cd "$ROOT"
MSE_ALLOW_MOCK_FALLBACK=0 PDF_CONVERTER_MODE=docker \
  PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_converter_strict.py -q
echo "  ✓ converter strict pytest"

if ! docker info >/dev/null 2>&1; then
  echo "SKIP live: Docker 不可用"
  exit 0
fi

for img in fudan-pager-maker fudan-pager-mineru; do
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    echo "构建镜像 $img ..."
    if [[ "$img" == "fudan-pager-maker" ]]; then
      docker build -f "$ROOT/docker/maker/Dockerfile" -t "$img" "$ROOT"
    else
      docker build -f "$ROOT/docker/mineru/Dockerfile" -t "$img" "$ROOT"
    fi
  fi
done

PDF="${MINERU_TEST_PDF:-}"
if [[ -z "$PDF" ]]; then
  PDF="$ROOT/samples/real_pdfs/arxiv_attention_is_all_you_need.pdf"
fi
if [[ ! -f "$PDF" ]]; then
  PDF=$(find "$ROOT/samples/real_pdfs" "$ROOT/samples" -name '*.pdf' 2>/dev/null | head -1 || true)
fi

if [[ -z "$PDF" || ! -f "$PDF" ]]; then
  echo "SKIP live PDF 上传: 设置 MINERU_TEST_PDF=/path/to/thesis.pdf 或放入 samples/*.pdf"
  echo "  ✓ 严格模式单元测试已通过"
  exit 0
fi

echo "=== 严格模式 API 上传测试 ($PDF) ==="
echo "NOTE: 需 API 以 MSE_ALLOW_MOCK_FALLBACK=0 PDF_CONVERTER_MODE=docker 重启"

rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }
ADV_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"mineru-$(rand)@local.test\",\"password\":\"secret12\",\"name\":\"M\",\"role\":\"advisor\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
STU="mineru-stu-$(rand)@local.test"
STU_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU\",\"password\":\"secret12\",\"name\":\"S\",\"role\":\"student\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

PID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"MinerU严格\",\"student_email\":\"$STU\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" -d '{"send_email":false}')
TOK=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\"}" >/dev/null

SUB=$(curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -F "file=@$PDF;filename=thesis.pdf;type=application/pdf")
ROUND=$(echo "$SUB" | python3 -c "import sys,json; print(json.load(sys.stdin)['round_number'])")
echo "  已提交真实 PDF，等待解析+分析（最多 180s）..."
STATUS=""
for i in $(seq 1 36); do
  sleep 5
  STATUS=$(curl -sf "$API/v1/mse/projects/$PID/rounds/$ROUND/report" \
    -H "Authorization: Bearer $ADV_TOKEN" \
    | python3 -c "import sys,json; print(json.load(sys.stdin, strict=False).get('review_status',''))" 2>/dev/null || echo "")
  echo "  [$i] $STATUS"
  case "$STATUS" in
    parsing|analyzing|pending|"") ;;
    *)
      break
      ;;
  esac
done
echo "  轮次 $ROUND 最终状态: $STATUS"
if [[ "$STATUS" == "parse_failed" ]]; then
  echo "  ✓ 严格模式：解析失败未 silently mock"
  exit 1
elif [[ "$STATUS" == "analysis_failed" ]]; then
  echo "  ✗ 分析失败"
  exit 1
elif [[ "$STATUS" == "parsing" || "$STATUS" == "analyzing" || "$STATUS" == "pending" ]]; then
  echo "  ✗ 超时仍在处理"
  exit 1
else
  echo "  ✓ MinerU + 分析流程完成: $STATUS"
fi
