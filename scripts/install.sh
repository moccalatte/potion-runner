#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/potion-runner"

if [[ $EUID -eq 0 ]]; then
  echo "Jalankan script ini sebagai user biasa dengan sudo password, bukan root langsung."
  exit 1
fi

sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER:$USER" "$APP_DIR"
rsync -a --delete ./ "$APP_DIR"/

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.lock"

install -m 600 /dev/null "$APP_DIR/.env"
cat ./.env.example > "$APP_DIR/.env"

sudo cp "$APP_DIR/ops/logrotate/potion-runner" /etc/logrotate.d/potion-runner
sudo cp "$APP_DIR/ops/systemd/potion-runner.service" /etc/systemd/system/
sudo cp "$APP_DIR/ops/systemd/potion-runner-backup.service" /etc/systemd/system/
sudo cp "$APP_DIR/ops/systemd/potion-runner-backup.timer" /etc/systemd/system/
sudo cp "$APP_DIR/ops/systemd/potion-runner-health.service" /etc/systemd/system/
sudo cp "$APP_DIR/ops/systemd/potion-runner-health.timer" /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now potion-runner.service
sudo systemctl enable --now potion-runner-backup.timer
sudo systemctl enable --now potion-runner-health.timer

echo "Instalasi dasar selesai. Edit $APP_DIR/.env untuk token & admin IDs."
