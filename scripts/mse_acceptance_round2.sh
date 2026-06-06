#!/usr/bin/env bash
# 第 2 轮提交 + diff 验收
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/mse_acceptance_lib.sh"
API="${API_BASE:-http://127.0.0.1:8000}"

rand() { python3 -c "import uuid; print(uuid.uuid4().hex[:8])"; }

ADV_EMAIL="adv-$(rand)@local.test"
STU_EMAIL="stu-$(rand)@local.test"

echo "=== Round 2 + Diff 验收 ==="

ADV_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADV_EMAIL\",\"password\":\"secret12\",\"name\":\"Adv\",\"role\":\"advisor\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
STU_TOKEN=$(curl -sf -X POST "$API/v1/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$STU_EMAIL\",\"password\":\"secret12\",\"name\":\"Stu\",\"role\":\"student\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

PID=$(curl -sf -X POST "$API/v1/mse/projects" \
  -H "Authorization: Bearer $ADV_TOKEN" -H "Content-Type: application/json" \
  -d "{\"title\":\"Diff验收\",\"student_email\":\"$STU_EMAIL\",\"auto_notify_student\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

INV=$(curl -sf -X POST "$API/v1/mse/projects/$PID/invite" \
  -H "Authorization: Bearer $ADV_TOKEN" -H "Content-Type: application/json" \
  -d "{\"send_email\":false}")
TOK=$(echo "$INV" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
curl -sf -X POST "$API/v1/mse/projects/$PID/accept" \
  -H "Authorization: Bearer $STU_TOKEN" -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOK\"}" >/dev/null

SAMPLE=$(mse_pick_submission_file "$ROOT")
for round in 1 2; do
  curl -sf -X POST "$API/v1/mse/projects/$PID/submissions" \
    -H "Authorization: Bearer $STU_TOKEN" \
    -F "file=@$SAMPLE;filename=$(mse_submission_filename "$SAMPLE");type=$(mse_submission_mime "$SAMPLE")" >/dev/null
  sleep 3
  if mse_is_strict_mode; then
    REPORT=$(curl -sf "$API/v1/mse/projects/$PID/rounds/$round/report" \
      -H "Authorization: Bearer $ADV_TOKEN")
    STATUS=$(echo "$REPORT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('review_status','unknown'))")
    if [[ "$STATUS" == "parse_failed" ]]; then
      echo "FAIL: strict conversion failed for round $round (status=$STATUS)" >&2
      exit 1
    fi
  fi
  echo "  完成第 ${round} 轮提交"
done

DIFF=$(curl -sf "$API/v1/mse/projects/$PID/rounds/2/diff?base=1" \
  -H "Authorization: Bearer $ADV_TOKEN")
echo "$DIFF" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"  diff: fixed={len(d.get('fixed',[]))} new={len(d.get('new',[]))} persistent={len(d.get('persistent',[]))}\")
assert d.get('base_round') == 1 and d.get('current_round') == 2
print('  OK GET .../rounds/2/diff?base=1')
"

DASH=$(curl -sf "$API/v1/mse/dashboard" -H "Authorization: Bearer $ADV_TOKEN")
echo "$DASH" | python3 -c "
import json, sys
d = json.load(sys.stdin)
s = d['advisor']['stats']
print(f\"  OK dashboard projects={s['total_projects']} active={s['active']}\")
"

echo "=== Round 2 + Diff 验收通过 ==="
