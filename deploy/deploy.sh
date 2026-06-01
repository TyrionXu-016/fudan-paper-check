#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOST="${DEPLOY_HOST:-114.55.139.240}"
USER="${DEPLOY_USER:-root}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check}"

if [[ -z "${DEPLOY_SSH_PASSWORD:-}" ]]; then
  echo "Set DEPLOY_SSH_PASSWORD or configure SSH key for ${USER}@${HOST}" >&2
  exit 1
fi

SSH="sshpass -p ${DEPLOY_SSH_PASSWORD} ssh -o StrictHostKeyChecking=no ${USER}@${HOST}"
RSYNC_SSH="sshpass -p ${DEPLOY_SSH_PASSWORD} ssh -o StrictHostKeyChecking=no"

echo "==> Sync ${ROOT} -> ${USER}@${HOST}:${REMOTE_DIR}"
rsync -az --delete \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude 'apps/web-next/node_modules' \
  --exclude 'apps/web-next/.next' \
  --exclude 'data' \
  --exclude '__pycache__' \
  --exclude '.cursor' \
  --exclude '*.docx' \
  --filter 'P deploy/.env.prod' \
  -e "${RSYNC_SSH}" \
  "${ROOT}/" "${USER}@${HOST}:${REMOTE_DIR}/"

echo "==> Build & restart containers"
${SSH} bash -s <<REMOTE
set -euo pipefail
cd ${REMOTE_DIR}
if [[ ! -f deploy/.env.prod ]]; then
  JWT=\$(openssl rand -hex 32)
  INVITE=\$(openssl rand -hex 32)
  cat > deploy/.env.prod <<EOF
JWT_SECRET=\${JWT}
MSE_INVITE_SECRET=\${INVITE}
CORS_ORIGINS=https://pager.tyrion.space,http://114.55.139.240,http://localhost:3000
APP_BASE_URL=https://pager.tyrion.space
MSE_DATABASE_URL=sqlite:////app/data/mse.db
PDF_CONVERTER_MODE=docker
MSE_ALLOW_MOCK_FALLBACK=0
MINERU_IMAGE=fudan-pager-mineru
MAKER_IMAGE=fudan-pager-maker
NOTIFIER=console
EOF
  chmod 600 deploy/.env.prod
fi
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.prod up -d --build
docker compose -f deploy/docker-compose.prod.yml ps
cp deploy/nginx/pager-api.tyrion.space.conf /etc/nginx/conf.d/pager-api.tyrion.space.conf
nginx -t
systemctl reload nginx
curl -sf http://127.0.0.1:18082/health
echo
curl -sf http://127.0.0.1:18082/v1/rule_bases | head -c 120
echo
REMOTE

echo "==> Deploy done"
