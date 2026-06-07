#!/usr/bin/env bash
set -euo pipefail

SSH_TARGET="${DEPLOY_SSH_TARGET:-mse}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check-mse}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-mse-tyrion}"
DEPLOY_REMOTE="${DEPLOY_REMOTE:-origin}"
DEPLOY_REPO="${DEPLOY_REPO:-git@github.com:TyrionXu-016/fudan-paper-check.git}"

echo "==> Deploy ${DEPLOY_BRANCH} on ${SSH_TARGET}:${REMOTE_DIR}"
ssh "${SSH_TARGET}" \
  "DEPLOY_DIR='${REMOTE_DIR}' DEPLOY_BRANCH='${DEPLOY_BRANCH}' DEPLOY_REMOTE='${DEPLOY_REMOTE}' DEPLOY_REPO='${DEPLOY_REPO}' bash -s" <<'REMOTE'
set -euo pipefail
if [[ ! -d "$DEPLOY_DIR/.git" ]]; then
  mkdir -p "$(dirname "$DEPLOY_DIR")"
  git clone --branch "$DEPLOY_BRANCH" "$DEPLOY_REPO" "$DEPLOY_DIR"
fi
cd "$DEPLOY_DIR"
git remote set-url "$DEPLOY_REMOTE" "$DEPLOY_REPO"
git fetch "$DEPLOY_REMOTE" "+refs/heads/${DEPLOY_BRANCH}:refs/remotes/${DEPLOY_REMOTE}/${DEPLOY_BRANCH}"
git checkout -B "$DEPLOY_BRANCH" "$DEPLOY_REMOTE/$DEPLOY_BRANCH"
git pull --ff-only "$DEPLOY_REMOTE" "$DEPLOY_BRANCH"
install -m 0644 deploy/nginx/api-mse.tyrion.space.conf /etc/nginx/conf.d/api-mse.tyrion.space.conf
nginx -t
systemctl reload nginx
DEPLOY_DIR="$DEPLOY_DIR" DEPLOY_BRANCH="$DEPLOY_BRANCH" DEPLOY_REMOTE="$DEPLOY_REMOTE" ./deploy/git-pull-deploy.sh
DEPLOY_DIR="$DEPLOY_DIR" DEPLOY_BRANCH="$DEPLOY_BRANCH" DEPLOY_REMOTE="$DEPLOY_REMOTE" ./deploy/install-auto-deploy.sh
REMOTE

echo "==> Deploy done"
