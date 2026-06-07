#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/fudan-pager-check}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-mse-tyrion}"
DEPLOY_REMOTE="${DEPLOY_REMOTE:-origin}"
SERVICE_NAME="${SERVICE_NAME:-fudan-pager-check-autodeploy}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"

if [[ "${EUID}" -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=Auto deploy fudan-pager-check backend when ${DEPLOY_BRANCH} changes
After=network-online.target docker.service
Wants=network-online.target docker.service

[Service]
Type=oneshot
WorkingDirectory=${DEPLOY_DIR}
Environment=DEPLOY_DIR=${DEPLOY_DIR}
Environment=DEPLOY_BRANCH=${DEPLOY_BRANCH}
Environment=DEPLOY_REMOTE=${DEPLOY_REMOTE}
ExecStart=${DEPLOY_DIR}/deploy/git-pull-deploy.sh --if-changed
TimeoutStartSec=3600
EOF

cat >"$TIMER_FILE" <<EOF
[Unit]
Description=Poll ${DEPLOY_BRANCH} for fudan-pager-check backend deploys

[Timer]
OnBootSec=30s
OnUnitActiveSec=60s
AccuracySec=10s
Unit=${SERVICE_NAME}.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.timer"
systemctl list-timers --all "${SERVICE_NAME}.timer" --no-pager
