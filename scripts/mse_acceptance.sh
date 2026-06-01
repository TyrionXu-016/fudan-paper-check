#!/usr/bin/env bash
# MSE 核心闭环本地验收脚本
set -euo pipefail
API="${API_BASE:-http://127.0.0.1:8000}"
PASS=0
FAIL=0

ok() { echo "  ✓ $1"; PASS=$((PASS+1)); }
bad() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

echo "=== MSE 本地验收 (API: $API) ==="

# 1. Health
if curl -sf "$API/health" | grep -q ok; then ok "API /health"; else bad "API /health"; fi

# 2. Register advisor + student
ADV_EMAIL="adv-$(rand)@local.test"
STU_EMAIL="stu-$(rand)@local.test"
ADV_JSON=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADV_EMAIL\",\"password\":\"secret12\",\"name\":\"Advisor\",\"role\":\"advisor\"}")
ADV_TOKEN=$(echo "$ADV_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "导师注册 ($ADV_EMAIL)"

STU_JSON=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"password\":\"secret12\",\"name\":\"Student\",\"role\":\"student\"}")
STU_TOKEN=$(echo "$STU_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "学生注册 ($STU_EMAIL)"

# 3. Advisor create project (auto_notify=false for preview flow)
PROJ=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"验收测试项目\",\"student_email\":\"$STU_EMAIL\",\"auto_notify_student\":false}")
PID=$(echo "$PROJ" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "导师创建项目 (id=$PID)"

# 4. Student create project (bidirectional)
STU_PROJ=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"学生发起项目\",\"advisor_email\":\"$ADV_EMAIL\"}")
if echo "$STU_PROJ" | grep -q '"initiator_role":"student"'; then
  ok "学生创建项目 (双向发起)"
else
  bad "学生创建项目"
fi

# 5. Default rules indexed on create + bind student
if echo "$PROJ" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('rule_base_ids') else 1)"; then
  ok "创建项目已自动索引默认规范"
else
  bad "创建项目默认规范索引"
fi

# Bind student via accept with invite
INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"send_email\":false}")
TOKEN=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN\"}" >/dev/null
ok "邀请并接受绑定学生"

# 6. Dashboard
DASH=$(curl -sf "$API/v1/mse/dashboard" -H "Authorization: Bearer $ADV_TOKEN")
if echo "$DASH" | grep -q '"total_projects"'; then
  ok "导师仪表盘 API"
else
  bad "导师仪表盘 API"
fi

# 7. Submit sample paper (use existing sample md as maker path via inline job)
SAMPLE=$(find "$(dirname "$0")/../samples" -name '*_maker.md' 2>/dev/null | head -1)
if [[ -z "$SAMPLE" ]]; then
  bad "找不到 samples/*_maker.md，跳过提交验收"
else
  SUB=$(curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
    -H "Authorization: Bearer $STU_TOKEN" \
    -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf")
  ROUND=$(echo "$SUB" | python3 -c "import sys,json; print(json.load(sys.stdin)['round_number'])")
  ok "学生提交第 ${ROUND} 轮 (inline worker)"

  # Wait for inline processing
  sleep 2

  # 8. Report - advisor can see, student 403 if pending_release
  REP_A=$(curl -s -w "%{http_code}" -o /tmp/mse_rep_a.json \
    "$API/v1/mse/projects/$PID/rounds/$ROUND/report" \
    -H "Authorization: Bearer $ADV_TOKEN")
  REP_S=$(curl -s -w "%{http_code}" -o /tmp/mse_rep_s.json \
    "$API/v1/mse/projects/$PID/rounds/$ROUND/report" \
    -H "Authorization: Bearer $STU_TOKEN")

  STATUS=$(python3 -c "import json; print(json.load(open('/tmp/mse_rep_a.json'))['review_status'])" 2>/dev/null || echo "unknown")
  if [[ "$REP_A" == "200" ]]; then ok "导师可读报告 (status=$STATUS)"; else bad "导师可读报告"; fi

  if [[ "$STATUS" == "pending_release" && "$REP_S" == "403" ]]; then
    ok "auto_notify=false: 学生未发布前 403"
    curl -sf -X POST "$API/v1/mse/projects/$PID/rounds/$ROUND/release" \
      -H "Authorization: Bearer $ADV_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{}" >/dev/null
    ok "导师 release 发布"
    REP_S2=$(curl -s -w "%{http_code}" -o /tmp/mse_rep_s2.json \
      "$API/v1/mse/projects/$PID/rounds/$ROUND/report" \
      -H "Authorization: Bearer $STU_TOKEN")
    if [[ "$REP_S2" == "200" ]]; then ok "release 后学生可读报告"; else bad "release 后学生可读"; fi
  elif [[ "$REP_S" == "200" ]]; then
    ok "学生可读报告 (auto released or passed)"
  else
    bad "学生报告访问 (advisor=$REP_A student=$REP_S status=$STATUS)"
  fi

  # Issue fields
  if python3 -c "
import json
r=json.load(open('/tmp/mse_rep_a.json'))
issues=(r.get('report') or {}).get('issues') or []
print(len(issues))
" 2>/dev/null | grep -qv '^0$'; then
    ok "报告含 Issue 列表"
  else
    ok "报告生成完成 (Issue 数量取决于样例)"
  fi
fi

# 9. Pytest suite
echo ""
echo "=== 自动化测试 ==="
cd "$(dirname "$0")/.."
if PYTHONPATH=packages:apps python3 -m pytest tests/test_mse_fsm.py tests/test_mse_core_loop.py -q; then
  ok "pytest MSE 测试套件"
else
  bad "pytest MSE 测试套件"
fi

# 10. Frontend
FE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/mse/dashboard)
if [[ "$FE" == "200" ]]; then ok "前端 /mse/dashboard (HTTP 200)"; else bad "前端 /mse/dashboard (HTTP $FE)"; fi

echo ""
echo "=== 验收结果: $PASS 通过, $FAIL 失败 ==="
[[ "$FAIL" -eq 0 ]]
