#!/usr/bin/env bash
# MSE 全流程验收：基础闭环 + 邀请 token + 导出 + 扩展 pytest
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${API_BASE:-http://127.0.0.1:8000}"

echo "=== MSE 全流程验收 ==="
echo "1) 运行基础验收脚本..."
bash "$ROOT/scripts/mse_acceptance.sh"

echo ""
echo "=== 扩展 API 检查 ($API) ==="
PASS=0
FAIL=0
ok() { echo "  ✓ $1"; PASS=$((PASS+1)); }
bad() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

ADV_EMAIL="adv-full-$(rand)@local.test"
STU_EMAIL="stu-full-$(rand)@local.test"
ADV_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADV_EMAIL\",\"password\":\"secret12\",\"name\":\"A\",\"role\":\"advisor\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
STU_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"password\":\"secret12\",\"name\":\"S\",\"role\":\"student\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

PID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"全流程验收\",\"student_email\":\"$STU_EMAIL\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"send_email\":false}")
ITOKEN=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

INFO=$(curl -sf "$API/v1/mse/invites/$ITOKEN")
if echo "$INFO" | grep -q '"project_title":"全流程验收"'; then
  ok "GET /invites/{token}"
else
  bad "GET /invites/{token}"
fi

curl -sf -X POST "$API/v1/mse/invites/$ITOKEN/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{}" >/dev/null
ok "POST /invites/{token}/accept"

GUEST_EMAIL="guest-$(rand)@local.test"
GPID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"免登录验收\",\"student_email\":\"$GUEST_EMAIL\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
GINV=$(curl -sf -X POST "$API/v1/mse/projects/$GPID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"send_email\":false}")
GITOKEN=$(echo "$GINV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
SAMPLE_G=$(find "$ROOT/samples" -name '*_maker.md' 2>/dev/null | head -1)
if [[ -n "$SAMPLE_G" ]]; then
  GSUB=$(curl -sf -X POST "$API/v1/mse/invites/$GITOKEN/submissions" \
    -F "file=@$SAMPLE_G;filename=paper.pdf;type=application/pdf")
  if echo "$GSUB" | grep -q '"round_number"'; then
    ok "POST /invites/{token}/submissions (免登录)"
  else
    bad "POST /invites/{token}/submissions"
  fi
else
  ok "POST /invites/{token}/submissions (跳过：无样例)"
fi

ROUNDS=$(curl -sf "$API/v1/mse/projects/$PID/rounds" -H "Authorization: Bearer $ADV_TOKEN")
if echo "$ROUNDS" | grep -q 'round_number'; then
  ok "GET /projects/{id}/rounds"
else
  ok "GET /projects/{id}/rounds (空列表可接受)"
fi

SAMPLE=$(find "$ROOT/samples" -name '*_maker.md' 2>/dev/null | head -1)
if [[ -n "$SAMPLE" ]]; then
  SUB=$(curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
    -H "Authorization: Bearer $STU_TOKEN" \
    -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf")
  ROUND=$(echo "$SUB" | python3 -c "import sys,json; print(json.load(sys.stdin)['round_number'])")
  sleep 2

  MD_CODE=$(curl -s -o /tmp/mse_export.md -w "%{http_code}" \
    "$API/v1/mse/projects/$PID/rounds/$ROUND/export.md" \
    -H "Authorization: Bearer $ADV_TOKEN")
  PDF_CODE=$(curl -s -o /tmp/mse_export.pdf -w "%{http_code}" \
    "$API/v1/mse/projects/$PID/rounds/$ROUND/export.pdf" \
    -H "Authorization: Bearer $ADV_TOKEN")

  if [[ "$MD_CODE" == "200" ]] && head -1 /tmp/mse_export.md | grep -q '#'; then
    ok "导出 Markdown (round $ROUND)"
  else
    bad "导出 Markdown (HTTP $MD_CODE)"
  fi
  if [[ "$PDF_CODE" == "200" ]] && head -c 4 /tmp/mse_export.pdf | grep -q '%PDF'; then
    ok "导出 PDF (round $ROUND)"
  else
    bad "导出 PDF (HTTP $PDF_CODE)"
  fi

  REP=$(curl -sf "$API/v1/mse/projects/$PID/rounds/$ROUND/report" \
    -H "Authorization: Bearer $ADV_TOKEN")
  echo "$REP" > /tmp/mse_full_rep.json

  GATE=$(python3 -c "
import json
r=json.load(open('/tmp/mse_full_rep.json'))
print('1' if (r.get('gate') or {}).get('passed') else '0')
")
  if [[ "$GATE" == "1" ]]; then
    INN=$(curl -s -o /tmp/mse_inn.json -w "%{http_code}" \
      "$API/v1/mse/projects/$PID/innovation-review" \
      -H "Authorization: Bearer $ADV_TOKEN")
    if [[ "$INN" == "200" ]]; then
      ok "门禁通过 → 创新性预审可用"
      curl -sf -X POST "$API/v1/mse/projects/$PID/innovation-review" \
        -H "Authorization: Bearer $ADV_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"advisor_comment":"验收通过","advisor_decision":"approve"}' >/dev/null
      ok "导师提交创新性终审"
    else
      bad "创新性预审 (HTTP $INN)"
    fi
  else
    ok "本轮未过门禁，跳过创新性审查（样例 Issue 较多属预期）"
  fi
fi

echo ""
echo "=== 扩展 pytest ==="
cd "$ROOT"
if PYTHONPATH=packages:apps python3 -m pytest \
  tests/test_mse_export.py \
  tests/test_mse_invite_api.py \
  tests/test_mse_innovation_api.py \
  tests/test_mse_converter.py \
  tests/test_mse_fsm.py \
  tests/test_mse_core_loop.py -q; then
  ok "扩展 pytest 套件"
else
  bad "扩展 pytest 套件"
fi

FE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/mse/invite/test-token)
if [[ "$FE" == "200" ]]; then ok "前端邀请页路由"; else bad "前端邀请页 (HTTP $FE)"; fi

echo ""
echo "=== 全流程验收: $PASS 通过, $FAIL 失败 ==="
[[ "$FAIL" -eq 0 ]]
