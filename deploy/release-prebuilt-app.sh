#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_TARGET="${DEPLOY_SSH_TARGET:-mse}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check-mse}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-mse-tyrion}"
DEPLOY_REMOTE="${DEPLOY_REMOTE:-origin}"
APP_IMAGE_PREFIX="${APP_IMAGE_PREFIX:-fudan-pager-mse-app}"
GIT_SHA="${GIT_SHA:-$(git -C "$ROOT" rev-parse --short=12 HEAD)}"
APP_IMAGE="${APP_IMAGE:-${APP_IMAGE_PREFIX}:${GIT_SHA}}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"
PYTHON_IMAGE="${PYTHON_IMAGE:-python:3.12-slim}"
ARCHIVE_DIR="${APP_IMAGE_ARCHIVE_DIR:-/tmp}"
ARCHIVE_NAME="$(printf '%s' "$APP_IMAGE" | tr '/:' '__').tar.gz"
ARCHIVE_PATH="${ARCHIVE_DIR}/${ARCHIVE_NAME}"
REMOTE_ARCHIVE="${REMOTE_ARCHIVE:-/tmp/${ARCHIVE_NAME}}"
ALLOW_DIRTY_BUILD="${ALLOW_DIRTY_BUILD:-0}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

quote() {
  printf '%q' "$1"
}

require_cmd docker
require_cmd gzip
require_cmd scp
require_cmd ssh

if [[ "$ALLOW_DIRTY_BUILD" != "1" ]]; then
  if ! git -C "$ROOT" diff --quiet || ! git -C "$ROOT" diff --cached --quiet; then
    echo "tracked worktree has local changes; commit or set ALLOW_DIRTY_BUILD=1" >&2
    exit 1
  fi
fi

if ! docker buildx version >/dev/null 2>&1; then
  echo "docker buildx is required to build ${DOCKER_PLATFORM} images off-host" >&2
  exit 1
fi

log "build ${APP_IMAGE} for ${DOCKER_PLATFORM}"
docker buildx build \
  --platform "$DOCKER_PLATFORM" \
  --build-arg "PYTHON_IMAGE=${PYTHON_IMAGE}" \
  --load \
  -t "$APP_IMAGE" \
  "$ROOT"

log "save ${APP_IMAGE} to ${ARCHIVE_PATH}"
docker save "$APP_IMAGE" | gzip -c >"$ARCHIVE_PATH"

log "upload image archive to ${SSH_TARGET}:${REMOTE_ARCHIVE}"
scp "$ARCHIVE_PATH" "${SSH_TARGET}:${REMOTE_ARCHIVE}"

log "load image and deploy on ${SSH_TARGET}"
ssh "$SSH_TARGET" \
  "DEPLOY_DIR=$(quote "$REMOTE_DIR") DEPLOY_BRANCH=$(quote "$DEPLOY_BRANCH") DEPLOY_REMOTE=$(quote "$DEPLOY_REMOTE") APP_IMAGE=$(quote "$APP_IMAGE") REMOTE_ARCHIVE=$(quote "$REMOTE_ARCHIVE") bash -s" <<'REMOTE'
set -euo pipefail

set_env_value() {
  local key="$1"
  local value="$2"
  local file="$3"
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
  ' "$file" >"$tmp"
  cat "$tmp" >"$file"
  rm -f "$tmp"
}

cd "$DEPLOY_DIR"
docker load -i "$REMOTE_ARCHIVE"
rm -f "$REMOTE_ARCHIVE"

git fetch --prune "$DEPLOY_REMOTE" \
  "+refs/heads/${DEPLOY_BRANCH}:refs/remotes/${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
git checkout -B "$DEPLOY_BRANCH" "${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
git pull --ff-only "$DEPLOY_REMOTE" "$DEPLOY_BRANCH"

mkdir -p deploy
touch deploy/.env.prod
chmod 600 deploy/.env.prod
set_env_value "APP_IMAGE" "$APP_IMAGE" deploy/.env.prod

DEPLOY_DIR="$DEPLOY_DIR" DEPLOY_BRANCH="$DEPLOY_BRANCH" DEPLOY_REMOTE="$DEPLOY_REMOTE" ./deploy/git-pull-deploy.sh
REMOTE

log "release finished with ${APP_IMAGE}"
