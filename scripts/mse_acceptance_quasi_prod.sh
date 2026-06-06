#!/usr/bin/env bash
# Local quasi-production MSE acceptance. Requires real MinerU, DeepSeek, SMTP, and a real public PDF.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ID="$(date +%Y%m%d%H%M%S)"
LOG_DIR="${MSE_ACCEPTANCE_LOG_DIR:-/tmp/mse_quasi_prod_$RUN_ID}"
API="${API_BASE:-http://127.0.0.1:8000}"
API_LOG="$LOG_DIR/api.log"
FE_LOG="$LOG_DIR/frontend.log"
API_PID=""
FE_PID=""

mkdir -p "$LOG_DIR"

cleanup() {
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$FE_PID" ]] && kill "$FE_PID" 2>/dev/null || true
}
trap cleanup EXIT

fail() {
  local stage="$1"
  local log="${2:-}"
  echo "FAIL: $stage"
  [[ -n "$log" ]] && echo "LOG: $log"
  exit 1
}

ok() {
  echo "OK: $1"
}

export_env() {
  local env_exports="$LOG_DIR/env.exports"
  (cd "$ROOT" && python3 - >"$env_exports" <<'PY'
from pathlib import Path
from dotenv import dotenv_values
import os
import re
import sys

prefixes = (
    "PYTHONPATH", "JOB_", "MSE_", "PDF_", "MINERU", "MAKER", "LLM_",
    "SMTP_", "NOTIFIER", "JWT_", "APP_", "API_BASE", "CORS_",
)
values = dict(os.environ)
values.update({k: v for k, v in dotenv_values(Path(".env")).items() if k and v is not None})
for key in sorted(k for k in values if k.startswith(prefixes)):
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        sys.stdout.buffer.write(f"{key}={values.get(key, '')}".encode("utf-8"))
        sys.stdout.buffer.write(bytes([0]))
PY
)
  while IFS= read -r -d '' assignment; do
    export "$assignment"
  done < "$env_exports"
  rm -f "$env_exports"
  export PYTHONPATH="${PYTHONPATH:-packages:apps}"
  export API_BASE="$API"
  export JOB_RUN_INLINE=1
  export PDF_CONVERTER_MODE=docker
  export MSE_ALLOW_MOCK_FALLBACK=0
  export MAKER_IMAGE="${MAKER_IMAGE:-fudan-pager-maker}"
  export MINERU_IMAGE="${MINERU_IMAGE:-fudan-pager-mineru}"
  export MINERU_BACKEND="${MINERU_BACKEND:-pipeline}"
  export MINERU_METHOD="${MINERU_METHOD:-txt}"
  export MINERU_START_PAGE="${MINERU_START_PAGE:-0}"
  export MINERU_END_PAGE="${MINERU_END_PAGE:-7}"
  export MINERU_PDF_RENDER_THREADS="${MINERU_PDF_RENDER_THREADS:-1}"
  export MINERU_PROCESSING_WINDOW_SIZE="${MINERU_PROCESSING_WINDOW_SIZE:-8}"
  export MINERU_FORMULA_ENABLE="${MINERU_FORMULA_ENABLE:-false}"
  export MINERU_TABLE_ENABLE="${MINERU_TABLE_ENABLE:-false}"
  export MINERU_DOCKER_SHM_SIZE="${MINERU_DOCKER_SHM_SIZE:-2g}"
  export MINERU_TIMEOUT_SECONDS="${MINERU_TIMEOUT_SECONDS:-1800}"
  export MINERU_CACHE_VOLUME="${MINERU_CACHE_VOLUME:-fudan-pager-mineru-cache}"
  export MSE_DATABASE_URL="${MSE_DATABASE_URL:-sqlite:///$ROOT/data/mse-quasi-prod.db}"
}

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    fail "missing required env $key"
  fi
}

run_stage() {
  local name="$1"
  shift
  local slug
  slug="$(echo "$name" | tr ' /' '__' | tr -cd '[:alnum:]_-.')"
  local log="$LOG_DIR/$slug.log"
  if (cd "$ROOT" && "$@") >"$log" 2>&1; then
    if grep -Eiq '(^|[^[:alpha:]])SKIP([^[:alpha:]]|$)' "$log"; then
      fail "$name emitted SKIP" "$log"
    fi
    ok "$name"
  else
    fail "$name" "$log"
  fi
}

wait_api() {
  for _ in $(seq 1 60); do
    if curl -sf "$API/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_frontend() {
  for _ in $(seq 1 90); do
    if curl -sf -o /dev/null "http://127.0.0.1:3000/mse/dashboard" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

ensure_port_free() {
  local port="$1"
  if lsof -iTCP:"$port" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    fail "port $port already in use"
  fi
}

export_env
run_stage "config status" python3 scripts/mse_config_status.py --quasi-prod-only
require_env LLM_API_KEY
require_env SMTP_HOST
export SMTP_TEST_STU="${SMTP_TEST_STU:-${SMTP_USER:-${SMTP_FROM:-}}}"
require_env SMTP_TEST_STU
if [[ "${NOTIFIER:-}" != "smtp" ]]; then
  fail "NOTIFIER must be smtp"
fi
if ! docker info >/dev/null 2>&1; then
  fail "docker is unavailable"
fi

PDF_LOG="$LOG_DIR/download_public_pdf.log"
PUBLIC_THESIS_PDF="$ROOT/samples/real_pdfs/public_cs_master_thesis.pdf"
if MINERU_TEST_PDF="$PUBLIC_THESIS_PDF" bash "$ROOT/scripts/download_mse_public_thesis_pdf.sh" >"$PDF_LOG" 2>&1; then
  export MINERU_TEST_PDF="$(tail -1 "$PDF_LOG")"
  [[ -f "$MINERU_TEST_PDF" ]] || fail "download public PDF" "$PDF_LOG"
  ok "download public PDF"
else
  fail "download public PDF" "$PDF_LOG"
fi

run_stage "build maker image" docker build -f docker/maker/Dockerfile -t "$MAKER_IMAGE" .
run_stage "build mineru image" docker build -f docker/mineru/Dockerfile -t "$MINERU_IMAGE" .
run_stage "python pytest" python3 -m pytest
run_stage "frontend lint" bash -c 'cd apps/web-next && npm run lint'
run_stage "frontend typecheck" bash -c 'cd apps/web-next && npx tsc --noEmit'
run_stage "frontend build" bash -c 'cd apps/web-next && npm run build'

ensure_port_free 8000
ensure_port_free 3000

(cd "$ROOT" && python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --app-dir apps) >"$API_LOG" 2>&1 &
API_PID="$!"
wait_api || fail "API startup" "$API_LOG"
ok "API startup"

(cd "$ROOT/apps/web-next" && npm run dev -- --port 3000) >"$FE_LOG" 2>&1 &
FE_PID="$!"
wait_frontend || fail "frontend startup" "$FE_LOG"
ok "frontend startup"

run_stage "mineru strict acceptance" bash scripts/mse_acceptance_mineru_strict.sh
run_stage "mse acceptance full" bash scripts/mse_acceptance_full.sh
run_stage "mse acceptance round2" bash scripts/mse_acceptance_round2.sh
run_stage "llm live acceptance" bash scripts/mse_acceptance_llm.sh
run_stage "smtp live acceptance" bash scripts/mse_acceptance_smtp.sh
if [[ "${MSE_ACCEPTANCE_EXTRA_LIVE:-0}" == "1" ]]; then
  run_stage "private sample live acceptance" python3 scripts/mse_acceptance_private_samples.py
  run_stage "webhook live acceptance" python3 scripts/mse_acceptance_webhook_live.py
fi

echo "OK: local quasi-production acceptance"
echo "LOG_DIR: $LOG_DIR"
