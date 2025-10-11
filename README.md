# Potion Runner Bot

Bot Telegram async berbasis `python-telegram-bot` v21 untuk memantau dan mengontrol node MCP/RAG pada laptop ASUS X450L. Proyek ini mengikuti _PRD potion runner_ dan memprioritaskan pengalaman pengguna ramah, logging real-time, backup otomatis, serta watchdog alert.

## Fitur Utama
- **Monitoring cepat**: CPU, RAM, disk (root & HDD), uptime, suhu (jika sensor), status layanan whitelist.
- **Kontrol aman**: start/stop/restart service systemd, update apt/pip/git dengan konfirmasi, audit log aksi.
- **Manajemen log**: tail runtime, grep error, kirim file log, akses journalctl service.
- **Backup rsync**: snapshot harian ke HDD `/mnt/potion-data`, manifest checksum, verifikasi.
- **Network tools**: info IP, ping host favorit, status Tailscale, speed test (opsional).
- **Alert & watchdog**: deteksi CPU/RAM/Disk/Suhu/Service fail dengan hysteresis, tulis `last_health.json`, kirim notifikasi ke admin.

## Struktur Folder
```
/opt/potion-runner/
├─ app/
│  ├─ bot.py
│  ├─ config.py
│  ├─ menus.py
│  ├─ handlers/
│  ├─ services/
│  └─ utils/
├─ logs/
├─ backups/
│  ├─ manifests/
│  └─ snapshots/
├─ requirements.lock
└─ .env
```
Semua path dapat dikustom melalui `.env`.

## Instalasi
Ikuti panduan langkah demi langkah pada [`docs/install.md`](docs/install.md). File tersebut menjelaskan:
1. Paket apt wajib.
2. Persiapan HDD 500 GB & fstab.
3. Pembuatan venv dan instal dependensi.
4. Penempatan kode ke `/opt/potion-runner/`.
5. Konfigurasi `.env`, logrotate, dan systemd service+timer.

## Menjalankan Bot Secara Manual
```bash
source /opt/potion-runner/venv/bin/activate
python -m app.bot
```
Pastikan `.env` berisi `BOT_TOKEN` dan `ADMIN_IDS` minimal satu ID admin.

## Menu & Perintah Penting
- `/start`, tombol ReplyKeyboard utama.
- `/status`, ringkas monitoring.
- `/svc <aksi> <service>`, kontrol service (admin).
- `/backup_now`, `/backup_list`, `/backup_verify`.
- `/log_runtime`, `/log_journal <service>`.
- `/ping [host]`, `/speed`, `/tailscale`.
- `/apt_update`, `/pip_sync`, `/git_pull`.
- `/set_backup HH:MM`, `/alerts`, `/alert_disable <kode> <menit>`.

## File Pendukung Sistem
Templates tersedia di folder `ops/`:
- `ops/systemd/potion-runner.service`
- `ops/systemd/potion-runner-backup.service`
- `ops/systemd/potion-runner-backup.timer`
- `ops/systemd/potion-runner-health.service`
- `ops/systemd/potion-runner-health.timer`
- `ops/logrotate/potion-runner`

Salin ke `/etc/systemd/system/` dan `/etc/logrotate.d/` sesuai petunjuk instalasi.

## Logging & Audit
- `logs/runtime.log` → log aplikasi real-time (rotate via logrotate).
- `logs/actions.log` → catatan siapa melakukan aksi apa.
- `journalctl -u potion-runner` → debug cepat service systemd.

## Backup & Restore
- Snapshot disimpan pada `backups/snapshots/<timestamp>`.
- Manifest checksum di `backups/manifests/<timestamp>.json`.
- Perintah manual tersedia di bot melalui menu Backup.

## Kode Gaya & Kontribusi
- Python 3.12+, async/await.
- File < 300 baris, modular (handlers/services/utils).
- Gunakan `run_cmd` wrapper untuk panggilan shell.

Selamat menggunakan Potion Runner Bot! 🧪
