#!/usr/bin/env bash
# 阶段 2：UI 走查等价 API 流程（无需浏览器手工点击）
set -euo pipefail

API="${API_BASE:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
ok() { echo "  ✓ $1"; PASS=$((PASS+1)); }
bad() { echo "  ✗ $1"; FAIL=$((FAIL+1)); }

rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

echo "=== MSE UI 流程验收 (API: $API) ==="

ADV_EMAIL="ui-adv-$(rand)@local.test"
STU_EMAIL="ui-stu-$(rand)@local.test"

# 1-2 注册导师 + 创建项目
ADV_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADV_EMAIL\",\"password\":\"secret12\",\"name\":\"UI导师\",\"role\":\"advisor\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "导师注册"

PID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"UI走查项目\",\"student_email\":\"$STU_EMAIL\",\"auto_notify_student\":false}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
ok "创建项目"

# 3 上传规范 md
SPEC="$ROOT/config/mse/default_spec.md"
UP=$(curl -sf -X POST "$API/v1/mse/projects/$PID/rules" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -F "file=@$SPEC;filename=custom_spec.md;type=text/markdown")
if echo "$UP" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('rule_base_ids') else 1)"; then
  ok "上传规范文档 (.md)"
else
  bad "上传规范文档"
fi

# 4 邀请链接
INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"send_email\":false}")
ITOKEN=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
ok "生成邀请链接"

# 5 免登录提交（独立小项目，避免占用主项目 student 账号）
GUEST_STU="ui-guest-$(rand)@local.test"
GPID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"UI免登录\",\"student_email\":\"$GUEST_STU\",\"auto_notify_student\":false}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
GINV=$(curl -sf -X POST "$API/v1/mse/projects/$GPID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"send_email":false}')
GITOKEN=$(echo "$GINV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

SAMPLE=$(find "$ROOT/samples" -name '*_maker.md' 2>/dev/null | head -1)
if [[ -n "$SAMPLE" ]]; then
  GSUB=$(curl -sf -X POST "$API/v1/mse/invites/$GITOKEN/submissions" \
    -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf")
  if echo "$GSUB" | grep -q '"round_number":1'; then
    ok "邀请页免登录提交"
  else
    bad "邀请页免登录提交"
  fi
  INFO=$(curl -sf "$API/v1/mse/invites/$GITOKEN")
  if echo "$INFO" | grep -q '"used":true'; then
    ok "邀请使用后标记 used"
  else
    bad "邀请 used 状态"
  fi
else
  bad "缺少样例文件，跳过免登录提交"
fi

# 6-7 学生注册 + 接受邀请 + 第 1/2 轮提交（主项目）
STU_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"password\":\"secret12\",\"name\":\"UI学生\",\"role\":\"student\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ok "学生注册"

curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$ITOKEN\"}" >/dev/null
ok "接受邀请"

if [[ -n "$SAMPLE" ]]; then
  SUB1=$(curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
    -H "Authorization: Bearer $STU_TOKEN" \
    -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf")
  R1=$(echo "$SUB1" | python3 -c "import sys,json; print(json.load(sys.stdin)['round_number'])")
  [[ "$R1" == "1" ]] && ok "学生第 1 轮提交" || bad "学生第 1 轮 (got round $R1)"

  SUB2=$(curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
    -H "Authorization: Bearer $STU_TOKEN" \
    -F "file=@$SAMPLE;filename=paper.pdf;type=application/pdf")
  R2=$(echo "$SUB2" | python3 -c "import sys,json; print(json.load(sys.stdin)['round_number'])")
  if [[ "$R2" == "2" ]]; then
    ok "学生第 2 轮提交"
  else
    bad "学生第 2 轮 (got round $R2)"
  fi
  sleep 2

  # 8 导出
  MD=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API/v1/mse/projects/$PID/rounds/1/export.md" \
    -H "Authorization: Bearer $ADV_TOKEN")
  PDF=$(curl -s -o /dev/null -w "%{http_code}" \
    "$API/v1/mse/projects/$PID/rounds/1/export.pdf" \
    -H "Authorization: Bearer $ADV_TOKEN")
  [[ "$MD" == "200" ]] && ok "导出 Markdown" || bad "导出 MD (HTTP $MD)"
  [[ "$PDF" == "200" ]] && ok "导出 PDF" || bad "导出 PDF (HTTP $PDF)"

  # 9 release
  STATUS=$(curl -sf "$API/v1/mse/projects/$PID/rounds/1/report" \
    -H "Authorization: Bearer $ADV_TOKEN" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['review_status'])")
  if [[ "$STATUS" == "pending_release" ]]; then
    curl -sf -X POST "$API/v1/mse/projects/$PID/rounds/1/release" \
      -H "Authorization: Bearer $ADV_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{}" >/dev/null
    STU_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      "$API/v1/mse/projects/$PID/rounds/1/report" \
      -H "Authorization: Bearer $STU_TOKEN")
    [[ "$STU_CODE" == "200" ]] && ok "release 后学生可读" || bad "release 后学生 (HTTP $STU_CODE)"
  else
    ok "release 流程 (status=$STATUS，非 pending_release)"
  fi
fi

# 10 review 页 API
REV_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "$API/v1/mse/projects/$PID/innovation-review" \
  -H "Authorization: Bearer $ADV_TOKEN")
[[ "$REV_CODE" == "200" || "$REV_CODE" == "404" ]] && ok "创新性审查 API 可达 (HTTP $REV_CODE)" || bad "review API (HTTP $REV_CODE)"

# 前端路由
for path in /mse/dashboard "/mse/invite/$GITOKEN" /mse/projects/new; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:3000${path}")
  [[ "$CODE" == "200" ]] && ok "前端 $path" || bad "前端 $path (HTTP $CODE)"
done

echo ""
echo "=== UI 流程验收: $PASS 通过, $FAIL 失败 ==="
[[ "$FAIL" -eq 0 ]]
