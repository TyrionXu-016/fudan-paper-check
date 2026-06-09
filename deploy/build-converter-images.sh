#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ENV_FILE:-deploy/.env.prod}"
MAKER_IMAGE="${MAKER_IMAGE:-fudan-pager-mse-maker}"
MINERU_IMAGE="${MINERU_IMAGE:-fudan-pager-mse-mineru}"

if [[ -f "$ROOT/$ENV_FILE" ]]; then
  maker_from_env="$(grep -m1 '^MAKER_IMAGE=' "$ROOT/$ENV_FILE" | cut -d= -f2- || true)"
  mineru_from_env="$(grep -m1 '^MINERU_IMAGE=' "$ROOT/$ENV_FILE" | cut -d= -f2- || true)"
  MAKER_IMAGE="${maker_from_env:-$MAKER_IMAGE}"
  MINERU_IMAGE="${mineru_from_env:-$MINERU_IMAGE}"
fi

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

log "build maker converter image ${MAKER_IMAGE}"
docker build -f "$ROOT/docker/maker/Dockerfile" -t "$MAKER_IMAGE" "$ROOT"

log "build mineru converter image ${MINERU_IMAGE}"
docker build -f "$ROOT/docker/mineru/Dockerfile" -t "$MINERU_IMAGE" "$ROOT"

log "converter images ready"
