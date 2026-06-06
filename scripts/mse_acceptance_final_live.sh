#!/usr/bin/env bash
# Full local live acceptance: quasi-prod gates + private sample + webhook live.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_ID="$(date +%Y%m%d%H%M%S)"
LOG_DIR="${MSE_ACCEPTANCE_LOG_DIR:-/tmp/mse_final_live_$RUN_ID}"
mkdir -p "$LOG_DIR"

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
    "SMTP_", "NOTIFIER", "JWT_", "APP_", "API_BASE", "CORS_", "WEBHOOK_",
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

export_env
run_stage "config status" python3 scripts/mse_config_status.py
export MSE_ACCEPTANCE_EXTRA_LIVE=1
export MSE_ACCEPTANCE_LOG_DIR="$LOG_DIR/quasi_prod"
run_stage "local quasi-production plus live extras" bash scripts/mse_acceptance_quasi_prod.sh

echo "OK: final live acceptance"
echo "LOG_DIR: $LOG_DIR"
