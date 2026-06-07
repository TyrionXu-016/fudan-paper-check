#!/usr/bin/env bash
# 在 DNS A 记录生效后于服务器上执行 HTTPS 配置
set -euo pipefail

DOMAIN="api-mse.tyrion.space"
EXPECTED_IP="114.55.139.240"
REMOTE_DIR="/opt/fudan-pager-check-mse"
NGINX_CONF="/etc/nginx/conf.d/api-mse.tyrion.space.conf"

echo "==> 检查 DNS: ${DOMAIN} -> ${EXPECTED_IP}"
RESOLVED=$(dig +short "@dns17.hichina.com" "${DOMAIN}" A | tail -1)
if [[ "${RESOLVED}" != "${EXPECTED_IP}" ]]; then
  echo "DNS 未生效。当前解析: ${RESOLVED:-（无记录）}" >&2
  echo "请在 tyrion.space 控制台确认 A 记录：主机记录 api-mse -> ${EXPECTED_IP}" >&2
  exit 1
fi

echo "==> 申请 Let's Encrypt 证书"
certbot certonly --nginx -d "${DOMAIN}" --non-interactive --agree-tos

echo "==> 更新 Nginx 配置"
cp "${REMOTE_DIR}/deploy/nginx/api-mse.tyrion.space.https.conf" "${NGINX_CONF}"
nginx -t
systemctl reload nginx

echo "==> 验证 HTTPS"
curl -sf "https://${DOMAIN}/health"
echo
echo "HTTPS 配置完成: https://${DOMAIN}"
