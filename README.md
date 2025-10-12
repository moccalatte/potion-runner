# Potion Runner Bot

Bot Telegram async berbasis `python-telegram-bot` v21 untuk memantau dan mengontrol node MCP/RAG pada laptop ASUS X450L. Proyek ini mengikuti _PRD potion runner_ dan memprioritaskan pengalaman pengguna ramah, logging real-time, backup otomatis, serta watchdog alert.

## Fitur Utama
- **Monitoring cepat**: CPU, RAM, disk (root & HDD), uptime, suhu (jika sensor), status layanan whitelist.
- **Kontrol aman**: start/stop/restart service systemd, update apt/pip/git dengan konfirmasi, audit log aksi.
- **Manajemen log**: tail runtime, grep error, kirim file log, akses journalctl service.
- **Backup rsync**: snapshot harian ke HDD `/mnt/potion-data`, manifest checksum, verifikasi.
- **Network tools**: info IP, ping host favorit, status Tailscale, speed test berbasis `speedtest-cli` (opsional).
- **Alert & watchdog**: deteksi CPU/RAM/Disk/Suhu/Service fail dengan hysteresis, tulis `last_health.json`, kirim notifikasi ke admin.
- **Pengaturan dinamis**: jadwal backup, threshold alert, dan whitelist service dapat diperbarui langsung dari bot (persist ke `.env`).
- **UI santai**: semua respons pakai gaya engineer friendly ala kurir digital supaya enak dibaca user.
- **Service control aman**: sistem mengharuskan sudo tanpa password untuk service whitelisted, dengan fallback log jika izin belum disetup.

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
4. Penempatan kode ke `APP_DIR` (default `/opt/potion-runner/`).
5. Konfigurasi `.env`, logrotate, dan systemd service+timer.
6. Konfigurasi sudoers agar user service bisa menjalankan `systemctl start/stop/restart` untuk layanan whitelist tanpa password.
7. (Opsional) Atur `SELF_SERVICE` di `.env` kalau nama unit bot berbeda dari `potion-runner.service`.
8. Untuk debug manual tanpa mematikan service, set `POTION_FORCE_RUN=1` sebelum `python -m app.bot` (pastikan instance lain sudah berhenti agar tidak ada konflik).

## Menjalankan Bot Secara Manual
```bash
source /opt/potion-runner/venv/bin/activate
python -m app.bot
```
Pastikan `.env` berisi `BOT_TOKEN` dan `ADMIN_IDS` minimal satu ID admin. Dependensi `python-telegram-bot` dipasang dengan ekstra `job-queue`, sehingga APScheduler tersedia untuk JobQueue internal. Format jadwal backup gunakan `HH:MM` (koma/ titik otomatis dikonversi).
Jika service systemd sudah aktif, hindari menjalankan `python -m app.bot` secara bersamaan karena Telegram hanya menerima satu koneksi polling.

## Menu & Perintah Penting
- `/start`, tombol ReplyKeyboard utama.
- `/status`, ringkas monitoring.
- `/svc <aksi> <service>`, kontrol service (admin).
- `/svc_list`, daftar whitelist dengan status terkini.
- `/backup_now`, `/backup_list`, `/backup_verify`.
- `/log_runtime`, `/log_journal <service>`.
- `/ping [host]`, `/speed`, `/tailscale`.
- `/apt_update`, `/pip_sync`, `/git_pull`.
- `/set_backup HH:MM`, `/alerts`, `/alert_disable <kode> <menit>`.
- `/set_threshold <metric> <nilai>`, kelola ambang alert.
- `/svc_add <service>`, `/svc_remove <service>` untuk update whitelist.
- `/uptime`, detail uptime + suhu.

## File Pendukung Sistem
Templates tersedia di folder `ops/`:
- `ops/systemd/potion-runner.service`
- `ops/systemd/potion-runner-backup.service`
- `ops/systemd/potion-runner-backup.timer`
- `ops/systemd/potion-runner-health.service`
- `ops/systemd/potion-runner-health.timer`
- `ops/logrotate/potion-runner`

Skrip pendukung:
- `scripts/update_timer.py` untuk sinkron jadwal timer systemd (dijalankan via sudo).

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
