#!/usr/bin/env bash
set -euo pipefail

BRANCH="${DEPLOY_BRANCH:-main}"
REMOTE="${DEPLOY_REMOTE:-origin}"
DOMAIN="${DEPLOY_DOMAIN:-paper-api.tyrion.space}"
APP_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check}"
ENV_FILE="${APP_DIR}/deploy/.env.prod"
NGINX_CONF="/etc/nginx/conf.d/${DOMAIN}.conf"

wait_for_url() {
  local url="$1"
  local attempts="${2:-30}"
  local delay="${3:-2}"
  local i
  for i in $(seq 1 "${attempts}"); do
    if curl -fsS "${url}"; then
      echo
      return 0
    fi
    sleep "${delay}"
  done
  echo "Timed out waiting for ${url}" >&2
  return 1
}

cd "${APP_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  JWT="$(openssl rand -hex 32)"
  cat > "${ENV_FILE}" <<EOF
JWT_SECRET=${JWT}
CORS_ORIGINS=https://paper.tyrion.space,https://${DOMAIN},http://${DOMAIN},http://114.55.139.240,http://localhost:3000
PDF_CONVERTER_MODE=docker
MAKER_IMAGE=fudan-pager-mse-maker
MINERU_IMAGE=
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

wait_for_url "http://127.0.0.1:18082/health"
wait_for_url "https://${DOMAIN}/health"
