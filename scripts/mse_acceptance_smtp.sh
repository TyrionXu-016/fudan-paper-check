#!/usr/bin/env bash
# 阶段 4：SMTP 验收 — 需在 mse_local.env 配置 NOTIFIER=smtp 及 SMTP_* 后重启 API
set -euo pipefail

API="${API_BASE:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/mse_acceptance_lib.sh"

if [[ "${NOTIFIER:-console}" != "smtp" ]] || [[ -z "${SMTP_HOST:-}" ]]; then
  echo "SKIP: 未配置 SMTP。请在项目根目录 .env 设置 NOTIFIER=smtp 和 SMTP_*，重启 API 后重试。"
  exit 0
fi

echo "=== SMTP 邮件验收 ==="
rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

ADV_EMAIL="${SMTP_TEST_ADV:-adv-smtp-$(rand)@local.test}"
STU_EMAIL="${SMTP_TEST_STU:-${SMTP_USER:-stu-smtp-$(rand)@local.test}}"

PYTHONPATH="$ROOT/packages:$ROOT/apps" SMTP_PREFLIGHT_TO="$STU_EMAIL" python3 - <<'PY'
import asyncio
import os
from notify.smtp import SmtpNotifier

async def main():
    to_email = os.environ["SMTP_PREFLIGHT_TO"]
    await SmtpNotifier().send(
        to_email,
        "[论文辅导] SMTP preflight",
        "<p>SMTP preflight succeeded.</p>",
        text_body="SMTP preflight succeeded.",
    )

asyncio.run(main())
PY
echo "  ✓ SMTP preflight 已发送"

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
  -d "{\"title\":\"SMTP验收\",\"student_email\":\"$STU_EMAIL\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "发送邀请邮件..."
curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"send_email\":true}" >/dev/null
echo "  ✓ 邀请邮件已触发（请检查 $STU_EMAIL 收件箱）"

INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"send_email\":false}")
TOK=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\"}" >/dev/null

SAMPLE=$(mse_pick_submission_file "$ROOT")
curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
  -H "Authorization: Bearer $STU_TOKEN" \
  -F "file=@$SAMPLE;filename=$(mse_submission_filename "$SAMPLE");type=$(mse_submission_mime "$SAMPLE")" >/dev/null
sleep 3
echo "  ✓ 提交完成，审查意见邮件应发往 $STU_EMAIL"
echo "=== 请人工确认收件箱 ==="
