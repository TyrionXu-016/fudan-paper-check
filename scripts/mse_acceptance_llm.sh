#!/usr/bin/env bash
# 阶段 3：LLM 验收 — 需在 scripts/mse_local.env 中配置 LLM_API_KEY 后 source 并重启 API
set -euo pipefail

API="${API_BASE:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ -z "${LLM_API_KEY:-}" ]]; then
  echo "SKIP: 未设置 LLM_API_KEY。请在项目根目录 .env 中配置 LLM_API_KEY，重启 API 后重试。"
  echo "运行 mock 测试..."
  cd "$ROOT"
  PYTHONPATH=packages:apps python3 -m pytest tests/test_innovation_agent.py tests/test_mse_innovation_api.py tests/test_mse_review_agent.py -q
  exit 0
fi

echo "=== LLM  live 验收 (DeepSeek) ==="
rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

ADV_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"llm-adv-$(rand)@local.test\",\"password\":\"secret12\",\"name\":\"L\",\"role\":\"advisor\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

STU="llm-stu-$(rand)@local.test"
PID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"LLM验收\",\"student_email\":\"$STU\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")


INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" -d '{"send_email":false}')
ITOKEN=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

STU_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU\",\"password\":\"secret12\",\"name\":\"S\",\"role\":\"student\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$ITOKEN\"}" >/dev/null

SAMPLE=$(find "$ROOT/samples" -name '*_maker.md' | head -1)
curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf" >/dev/null

echo "等待 LLM 分析 (最多 120s)..."
for i in $(seq 1 24); do
  sleep 5
  REP=$(curl -sf "$API/v1/mse/projects/$PID/rounds/1/report" -H "Authorization: Bearer $ADV_TOKEN")
  STATUS=$(echo "$REP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('review_status',''))")
  if [[ "$STATUS" != "analyzing" && "$STATUS" != "parsing" && "$STATUS" != "pending" ]]; then
    echo "  轮次状态: $STATUS"
    echo "$REP" | python3 -c "
import sys,json
r=json.load(sys.stdin)
issues=(r.get('report') or {}).get('issues') or []
llm=sum(1 for i in issues if getattr(i.get('issue_type'),'str',i.get('issue_type'))=='llm' or i.get('issue_type')=='llm')
print(f'  Issue 总数={len(issues)} llm类型={llm}')
gate=r.get('gate') or {}
print(f'  门禁 passed={gate.get(\"passed\")}')
"
    GATE=$(echo "$REP" | python3 -c "import sys,json; print((json.load(sys.stdin).get('gate') or {}).get('passed'))")
    if [[ "$GATE" == "True" ]]; then
      curl -sf "$API/v1/mse/projects/$PID/innovation-review" -H "Authorization: Bearer $ADV_TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('  创新性预审:', 'summary' in d or 'llm_summary' in str(d))
"
    fi
    exit 0
  fi
done
echo "FAIL: 分析超时"
exit 1
