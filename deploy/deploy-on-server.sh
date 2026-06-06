#!/usr/bin/env bash
set -euo pipefail

BRANCH="${DEPLOY_BRANCH:-main}"
REMOTE="${DEPLOY_REMOTE:-origin}"
DOMAIN="${DEPLOY_DOMAIN:-paper-api.tyrion.space}"
APP_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check}"
ENV_FILE="${APP_DIR}/deploy/.env.prod"
NGINX_CONF="/etc/nginx/conf.d/${DOMAIN}.conf"

cd "${APP_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  JWT="$(openssl rand -hex 32)"
  cat > "${ENV_FILE}" <<EOF
JWT_SECRET=${JWT}
CORS_ORIGINS=https://pager.tyrion.space,https://${DOMAIN},http://${DOMAIN},http://114.55.139.240,http://localhost:3000
PDF_CONVERTER_MODE=mock
EOF
  chmod 600 "${ENV_FILE}"
fi

git fetch "${REMOTE}" "${BRANCH}"
git checkout "${BRANCH}"
git pull --ff-only "${REMOTE}" "${BRANCH}"

cp "deploy/nginx/${DOMAIN}.conf" "${NGINX_CONF}"
nginx -t
systemctl reload nginx

docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.prod up -d --build
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.prod ps

curl -fsS "http://127.0.0.1:18082/health"
echo
curl -fsS "https://${DOMAIN}/health"
echo
