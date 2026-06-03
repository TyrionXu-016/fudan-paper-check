#!/usr/bin/env bash
# 全自动 MSE 功能验收（无需人工介入）：加载 .env → 重启 API → 跑各阶段脚本 + pytest
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${API_BASE:-http://127.0.0.1:8000}"
LOG="/tmp/mse_acceptance_auto.log"
API_LOG="/tmp/mse_api_acceptance.log"
PASS=0
FAIL=0

ok() { echo "  ✓ $1"; PASS=$((PASS + 1)); }
bad() { echo "  ✗ $1"; FAIL=$((FAIL + 1)); }

export_env() {
  eval "$(cd "$ROOT" && python3 -c "
from pathlib import Path
from dotenv import load_dotenv
import os, shlex
load_dotenv(Path('.env'), override=True)
keys = [k for k in os.environ if k.startswith((
    'PYTHONPATH','JOB_','MSE_','PDF_','MINERU','MAKER','LLM_','SMTP_','NOTIFIER',
    'JWT_','APP_','API_BASE'
))]
for k in sorted(set(keys)):
    v = os.environ.get(k, '')
    print(f'export {k}={shlex.quote(v)}')
")"
  export PYTHONPATH="${PYTHONPATH:-packages:apps}"
  export API_BASE="$API"
}

wait_api() {
  for _ in $(seq 1 40); do
    if curl -sf "$API/health" | grep -q ok; then
      return 0
    fi
    sleep 1
  done
  return 1
}

start_api() {
  lsof -ti:8000 2>/dev/null | xargs kill 2>/dev/null || true
  sleep 1
  cd "$ROOT"
  export_env
  nohup python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --app-dir apps \
    >"$API_LOG" 2>&1 &
  echo $! > /tmp/mse_api_acceptance.pid
  if wait_api; then
    ok "API 已启动 ($API)"
  else
    bad "API 启动失败，见 $API_LOG"
    tail -30 "$API_LOG" || true
    exit 1
  fi
}

fe_ok() {
  curl -sf -o /dev/null "http://127.0.0.1:3000/mse/dashboard" 2>/dev/null
}

start_frontend() {
  if fe_ok; then
    ok "前端已运行 (3000)"
    return 0
  fi
  echo "启动 Next.js 开发服务..."
  cd "$ROOT/apps/web-next"
  nohup npm run dev -- --port 3000 > /tmp/mse_fe_acceptance.log 2>&1 &
  echo $! > /tmp/mse_fe_acceptance.pid
  for _ in $(seq 1 90); do
    if fe_ok; then
      ok "前端已启动 (3000)"
      return 0
    fi
    sleep 2
  done
  bad "前端启动失败，见 /tmp/mse_fe_acceptance.log"
  tail -20 /tmp/mse_fe_acceptance.log 2>/dev/null || true
  return 1
}

run_stage() {
  local name="$1"
  shift
  echo ""
  echo "=== $name ==="
  if (cd "$ROOT" && export_env && "$@") >>"$LOG" 2>&1; then
    ok "$name"
    return 0
  else
    bad "$name failed; see tail of $LOG"
    tail -40 "$LOG" || true
    return 1
  fi
}

: >"$LOG"
echo "=== MSE 全自动验收 ===" | tee -a "$LOG"
start_api
start_frontend || true

run_stage "pytest 核心套件" bash -c 'PYTHONPATH=packages:apps python3 -m pytest \
  tests/test_mse_fsm.py tests/test_mse_core_loop.py \
  tests/test_mse_default_rules_bootstrap.py tests/test_mse_converter_strict.py -q'

run_stage "基础闭环 mse_acceptance.sh" bash scripts/mse_acceptance.sh

run_stage "全流程 mse_acceptance_full.sh" bash scripts/mse_acceptance_full.sh

if docker info >/dev/null 2>&1; then
  for img in fudan-pager-maker fudan-pager-mineru; do
    docker image inspect "$img" >/dev/null 2>&1 || {
      echo "构建 $img ..."
      if [[ "$img" == fudan-pager-maker ]]; then
        docker build -f "$ROOT/docker/maker/Dockerfile" -t "$img" "$ROOT" -q
      else
        docker build -f "$ROOT/docker/mineru/Dockerfile" -t "$img" "$ROOT" -q
      fi
    }
  done
  run_stage "MinerU 严格模式" bash scripts/mse_acceptance_mineru_strict.sh
else
  bad "Docker 不可用，跳过 MinerU 严格模式"
fi

if [[ -n "${LLM_API_KEY:-}" ]]; then
  run_stage "LLM 验收" bash scripts/mse_acceptance_llm.sh
else
  echo "SKIP LLM live（无 LLM_API_KEY）"
fi

if [[ "${NOTIFIER:-}" == "smtp" && -n "${SMTP_HOST:-}" ]]; then
  run_stage "SMTP 验收" bash scripts/mse_acceptance_smtp.sh
else
  echo "SKIP SMTP live"
fi

echo ""
echo "=== 验收汇总: $PASS 项通过, $FAIL 项失败 ==="
echo "完整日志: $LOG"
echo "API 日志: $API_LOG"
[[ "$FAIL" -eq 0 ]]
