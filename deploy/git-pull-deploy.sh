#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check-mse}"
DEPLOY_REMOTE="${DEPLOY_REMOTE:-origin}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-mse-tyrion}"
COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-deploy/.env.prod}"
LOCK_FILE="${LOCK_FILE:-/var/lock/fudan-pager-check-mse-deploy.lock}"
API_HEALTH_URL="${API_HEALTH_URL:-http://127.0.0.1:18083/health}"
export DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"
export COMPOSE_DOCKER_CLI_BUILD="${COMPOSE_DOCKER_CLI_BUILD:-0}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

set_env_value() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  awk -v key="$key" -v value="$value" '
    BEGIN { done = 0 }
    $0 ~ "^" key "=" {
      if (!done) {
        print key "=" value
        done = 1
      }
      next
    }
    { print }
    END {
      if (!done) {
        print key "=" value
      }
    }
  ' "$ENV_FILE" >"$tmp"
  cat "$tmp" >"$ENV_FILE"
  rm -f "$tmp"
}

set_env_default() {
  local key="$1"
  local value="$2"
  local current
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    current="$(grep -m1 "^${key}=" "$ENV_FILE" | cut -d= -f2-)"
    if [[ -z "$current" ]]; then
      set_env_value "$key" "$value"
    fi
  else
    printf '%s=%s\n' "$key" "$value" >>"$ENV_FILE"
  fi
}

append_cors_origin() {
  local origin="$1"
  local current
  current="$(grep -m1 '^CORS_ORIGINS=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"
  if [[ -z "$current" || "$current" == "*" ]]; then
    current="$origin"
  elif [[ ",$current," != *",$origin,"* ]]; then
    current="${current},${origin}"
  fi
  set_env_value "CORS_ORIGINS" "$current"
}

ensure_env_file() {
  mkdir -p "$(dirname "$ENV_FILE")"
  if [[ ! -f "$ENV_FILE" ]]; then
    umask 077
    cat >"$ENV_FILE" <<EOF
JWT_SECRET=$(openssl rand -hex 32)
MSE_INVITE_SECRET=$(openssl rand -hex 32)
CORS_ORIGINS=https://mse.paper.tyrion.space,https://api-mse.tyrion.space,http://api-mse.tyrion.space,http://114.55.139.240,http://localhost:3000
APP_BASE_URL=https://mse.paper.tyrion.space
MSE_DATABASE_URL=sqlite:////app/data/mse.db
PDF_CONVERTER_MODE=docker
MSE_ALLOW_MOCK_FALLBACK=0
MINERU_IMAGE=fudan-pager-mse-mineru
MAKER_IMAGE=fudan-pager-mse-maker
MINERU_BACKEND=pipeline
MINERU_METHOD=auto
MINERU_MAX_RETRIES=2
MINERU_TIMEOUT_SECONDS=1800
MINERU_CACHE_VOLUME=fudan-pager-mse-mineru-cache
NOTIFIER=console
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
LLM_MODEL_REASONING=deepseek-reasoner
EOF
  else
    chmod 600 "$ENV_FILE"
  fi

  set_env_default "JWT_SECRET" "$(openssl rand -hex 32)"
  set_env_default "MSE_INVITE_SECRET" "$(openssl rand -hex 32)"
  set_env_value "APP_BASE_URL" "https://mse.paper.tyrion.space"
  set_env_default "MSE_DATABASE_URL" "sqlite:////app/data/mse.db"
  set_env_value "PDF_CONVERTER_MODE" "docker"
  set_env_value "MSE_ALLOW_MOCK_FALLBACK" "0"
  set_env_default "MINERU_IMAGE" "fudan-pager-mse-mineru"
  set_env_default "MAKER_IMAGE" "fudan-pager-mse-maker"
  set_env_default "MINERU_BACKEND" "pipeline"
  set_env_default "MINERU_METHOD" "auto"
  set_env_default "MINERU_MAX_RETRIES" "2"
  set_env_default "MINERU_TIMEOUT_SECONDS" "1800"
  set_env_default "MINERU_CACHE_VOLUME" "fudan-pager-mse-mineru-cache"
  set_env_default "NOTIFIER" "console"
  set_env_default "LLM_PROVIDER" "deepseek"
  set_env_default "LLM_BASE_URL" "https://api.deepseek.com/v1"
  set_env_default "LLM_MODEL" "deepseek-chat"
  set_env_default "LLM_MODEL_REASONING" "deepseek-reasoner"
  set_env_default "MSE_REVISION_DUE_DAYS" "7"
  set_env_default "MSE_REVISION_REMINDER_WINDOW_HOURS" "24"
  set_env_default "MSE_REVISION_REMINDER_DRY_RUN" "0"
  append_cors_origin "https://api-mse.tyrion.space"
  append_cors_origin "http://api-mse.tyrion.space"
  append_cors_origin "https://mse.paper.tyrion.space"
  chmod 600 "$ENV_FILE"
}

wait_for_health() {
  local attempt
  for attempt in $(seq 1 30); do
    if curl -fsS "$API_HEALTH_URL" >/dev/null; then
      return 0
    fi
    log "health check retry ${attempt}/30"
    sleep 2
  done
  curl -fsS "$API_HEALTH_URL" >/dev/null
}

main() {
  require_cmd git
  require_cmd docker
  require_cmd curl
  require_cmd openssl
  require_cmd flock
  mkdir -p "$(dirname "$LOCK_FILE")"
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    log "deploy already running; exiting"
    exit 0
  fi

  cd "$DEPLOY_DIR"
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "tracked worktree has local changes; refusing deploy" >&2
    exit 1
  fi

  log "fetch ${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
  git fetch --prune "$DEPLOY_REMOTE" \
    "+refs/heads/${DEPLOY_BRANCH}:refs/remotes/${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
  local target current
  target="$(git rev-parse "${DEPLOY_REMOTE}/${DEPLOY_BRANCH}")"
  current="$(git rev-parse HEAD)"
  if [[ "${1:-}" == "--if-changed" && "$current" == "$target" ]]; then
    log "no branch changes"
    exit 0
  fi

  log "checkout ${DEPLOY_BRANCH}"
  git checkout -B "$DEPLOY_BRANCH" "${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
  git pull --ff-only "$DEPLOY_REMOTE" "$DEPLOY_BRANCH"

  ensure_env_file

  log "build converter images"
  docker build -f docker/maker/Dockerfile -t "$(grep -m1 '^MAKER_IMAGE=' "$ENV_FILE" | cut -d= -f2-)" .
  docker build -f docker/mineru/Dockerfile -t "$(grep -m1 '^MINERU_IMAGE=' "$ENV_FILE" | cut -d= -f2-)" .

  log "build and restart backend containers"
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build --remove-orphans
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

  log "health check"
  wait_for_health
  log "deploy finished"
}

main "$@"
