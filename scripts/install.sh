#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
APP_DIR="${APP_DIR:-/opt/potion-runner}"
SERVICE_USER="${SERVICE_USER:-$USER}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Script ---
if [[ $EUID -eq 0 ]]; then
  echo "Jalankan script ini sebagai user biasa dengan sudo password, bukan root langsung."
  exit 1
fi

echo ">>> Menyiapkan direktori aplikasi di $APP_DIR..."
sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER:$USER" "$APP_DIR"
rsync -a --delete --exclude ".git" --exclude "tests/" "$REPO_ROOT"/ "$APP_DIR"/

echo ">>> Membuat virtualenv dan menginstall dependensi..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.lock"
echo "Dependensi python-telegram-bot terpasang dengan ekstra job-queue (APScheduler aktif)."

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo ">>> Membuat file .env dari template..."
  install -m 600 /dev/null "$APP_DIR/.env"
  cat "$REPO_ROOT/.env.example" > "$APP_DIR/.env"
else
  echo ">>> File .env sudah ada, tidak ditimpa."
fi

ensure_env() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "$APP_DIR/.env"; then
    sed -i "s|^${key}=.*|${key}=\"${value}\"|" "$APP_DIR/.env"
  else
    printf '%s="%s"\n' "$key" "$value" >> "$APP_DIR/.env"
  fi
}

echo ">>> Memastikan path di .env sudah benar..."
ensure_env "DATA_DIR" "$APP_DIR"
ensure_env "LOG_DIR" "$APP_DIR/logs"
ensure_env "BACKUP_DIR" "$APP_DIR/backups"

install_systemd_unit() {
    local unit_file="$1"
    local exec_start="$2"

    echo ">>> Menginstall unit systemd: $unit_file"
    sudo cp "$APP_DIR/ops/systemd/$unit_file" "/etc/systemd/system/"
    sudo sed -i "s|^User=.*|User=$SERVICE_USER|" "/etc/systemd/system/$unit_file"
    sudo sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$APP_DIR|" "/etc/systemd/system/$unit_file"
    sudo sed -i "s|^ExecStart=.*|ExecStart=$exec_start|" "/etc/systemd/system/$unit_file"
}

install_systemd_unit "potion-runner.service" "$APP_DIR/venv/bin/python -m app.bot"
install_systemd_unit "potion-runner-backup.service" "$APP_DIR/venv/bin/python $APP_DIR/scripts/backup_once.py"
install_systemd_unit "potion-runner-health.service" "$APP_DIR/venv/bin/python $APP_DIR/scripts/health_ping.py"

echo ">>> Menginstall timer systemd..."
sudo cp "$APP_DIR/ops/systemd/potion-runner-backup.timer" /etc/systemd/system/
sudo cp "$APP_DIR/ops/systemd/potion-runner-health.timer" /etc/systemd/system/

echo ">>> Menginstall logrotate config..."
sudo cp "$APP_DIR/ops/logrotate/potion-runner" /etc/logrotate.d/potion-runner

echo ">>> Me-reload daemon systemd dan mengaktifkan service..."
sudo systemctl daemon-reload
sudo systemctl enable --now potion-runner.service
sudo systemctl enable --now potion-runner-backup.timer
sudo systemctl enable --now potion-runner-health.timer

sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

echo ">>> Instalasi dasar selesai. Edit $APP_DIR/.env untuk token & admin IDs."
