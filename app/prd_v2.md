# PRD — Telegram Bot Pantau/Control **potion-runner**

> **Context**: Laptop jadul **ASUS X450L** (Intel i5‑4210U, RAM 8 GB, SSD 256 GB + HDD 500 GB), OS **Kubuntu/Ubuntu 24.04 LTS** (headless/SSH). Bot Telegram dipakai untuk memantau & mengontrol node runner MCP/RAG/tools, dengan fokus **ringan tapi advanced**, aman, tahan error (mati lampu, hang), serta **otomatis backup** ke HDD 500 GB.

> **User level**: Pemula Linux. Semua langkah step‑by‑step, aman default, dan jelaskan istilah penting secara singkat.

---

## 1) Tujuan Produk

- **Pantau** server jadul: CPU/RAM/disk, health, service status, log runtime.
- **Kontrol** dasar: start/stop/restart service, reboot/shutdown aman, jalankan skrip rutin (pull repo, update, backup).
- **Notifikasi**: error, service mati, disk full, suhu tinggi, koneksi putus/nyambung.
- **Backup otomatis**: konfigurasi, log, dan artefak ringan ke **HDD 500 GB** (partisi khusus).
- **Ramah pengguna**: menu **ReplyKeyboardMarkup + emoji**; bahasa santai ala aplikasi kurir (pesan *processing* → lalu *done/failed*).
- **Tahan gangguan**: auto‑restart, watchdog, log rotate, recovery setelah listrik padam.

**Non‑Goals**
- Bukan panel full‑blown seperti Portainer/Netdata (bisa integrasi link).
- Bukan deployment multi‑node (namun desain mudah diekspansi).

---

## 2) Arsitektur Ringkas (Layered)

**Layer 1 – Infrastruktur OS**
- Ubuntu 24.04 (server/headless), user non‑root `dre` + sudo.
- **systemd** untuk daemon bot & timer (backup, health check).
- **journald + logrotate** untuk log aman.
- **fstab** mount HDD 500 GB by UUID → `/mnt/potion-data` (ext4, `noatime`), folder data: backups, logs, dumps.

**Layer 2 – Runtime Aplikasi (Python venv)**
- Python 3.12+, `venv` terisolasi: `/opt/potion-runner/venv`.
- Library utama: **python-telegram-bot v21+ (async)**, `psutil`, `python-dotenv`, `aiofiles`, `pyyaml`.
- Struktur repo standar, logging konsol + file `runtime.log` (rotated) **realtime**.

**Layer 3 – Bot & Service Adapters**
- Modul “Use‑Cases”:
  - Monitoring (CPU/RAM/disk/temp, uptime).
  - Controls (systemctl actions, reboot/shutdown aman).
  - Logs (tail, grep error, share file).
  - Backup/Restore.
  - Network (IP, ping, speed quick, Tailscale status opsional).
  - Updates (apt, pip, pull repos).
- Modul “Adapters”: wrapper `systemctl`, `journalctl`, `rsync`, `lsblk`, `smartctl` (opsional), `tailscale` (opsional).

**Layer 4 – UI Telegram**
- **ReplyKeyboardMarkup** + emoji, teks ramah:
  - Saat proses lama → kirim pesan: *"Oke, lagi aku cek dulu server kamu. Sabar sebentar ya ⚙️"*
  - Setelah selesai → kirim *sukses* atau *gagal* + ringkasan.

**Layer 5 – Observability & Recovery**
- File log: app (`runtime.log`), audit tindakan, job scheduler.
- **systemd Restart=always**, WatchdogSec, `StartLimitIntervalSec` + `StartLimitBurst`.
- **Backup** terjadwal (rsync) + **checksum**; restore cepat.

---

## 3) Keputusan Teknis (Why)

- **python-telegram-bot (PTB) v21**: Stable, async, ekosistem besar. Alternatif: `aiogram` (ringan), tapi PTB lebih umum contoh untuk pemula.
- **venv wajib**: isolasi dependensi, aman update.
- **systemd units**: start otomatis saat boot, auto‑restart saat crash.
- **HDD ext4**: sederhana, aman dari korup karena journaling; `noatime` mengurangi write.
- **rsync**: cepat, hemat bandwidth/disk, bisa incremental.
- **logrotate**: cegah disk penuh.

---

## 4) Struktur Folder & File

```
/opt/potion-runner/
├─ app/
│  ├─ bot.py                 # titik masuk bot (async PTB)
│  ├─ config.py              # load .env, path, constants
│  ├─ menus.py               # ReplyKeyboard & teks template
│  ├─ handlers/
│  │   ├─ start.py           # /start, menu utama
│  │   ├─ monitoring.py      # CPU/RAM/Disk/temp/uptime
│  │   ├─ controls.py        # start/stop/restart, reboot, shutdown
│  │   ├─ logs.py            # tail, grep, kirim file log
│  │   ├─ backup.py          # manual backup/restore
│  │   ├─ network.py         # IP, ping, speed quick, tailscale status
│  │   ├─ updates.py         # apt/pip, git pull
│  │   └─ admin.py           # whitelist admin, broadcast, diag
│  ├─ services/
│  │   ├─ sysctl.py          # adapter systemctl/journalctl
│  │   ├─ metrics.py         # psutil, suhu (lm-sensors)
│  │   ├─ backup_svc.py      # rsync, manifest json + checksum
│  │   ├─ hdd.py             # mount check, smartctl (opsional)
│  │   └─ net.py             # ip addr, ping, speed (iperf/fastcli opsional)
│  ├─ utils/
│  │   ├─ logging.py         # logger ke console + file runtime.log (realtime)
│  │   ├─ shell.py           # run_cmd() aman, timeout, return code
│  │   └─ format.py          # tabel teks, byte→GB, emoji gauge
│  └─ __init__.py
├─ .env                      # BOT_TOKEN, ADMIN_IDS, PATHS..
├─ requirements.lock         # output pip freeze
├─ venv/                     # virtualenv
├─ logs/
│  ├─ runtime.log            # log utama (rotate)
│  └─ actions.log            # audit perintah via bot
└─ backups/
   ├─ manifests/             # daftar file & checksum
   └─ snapshots/             # hasil rsync per tanggal
```

**Data di HDD** (direkomendasikan): mount ke `/mnt/potion-data` lalu symlink:
```
/mnt/potion-data/
├─ potion-runner-logs/      → symlink dari /opt/potion-runner/logs
├─ potion-runner-backups/   → symlink dari /opt/potion-runner/backups
└─ dumps/
```

---

## 5) Dependensi & Paket

- **APT**: `python3-venv`, `python3-pip`, `git`, `rsync`, `lm-sensors`, `htop`, `sysstat`, `smartmontools` (opsional), `tailscale` (opsional), `acl`.
- **PIP** (di venv): `python-telegram-bot~=21.6`, `psutil`, `python-dotenv`, `aiofiles`, `PyYAML`.

> Catatan singkat:
> - `lm-sensors` untuk baca suhu (jalankan `sudo sensors-detect` sekali).
> - `smartmontools` hanya jika butuh SMART disk health.

---

## 6) Env Vars (.env)

```
BOT_TOKEN="123:ABC..."           # token Telegram
ADMIN_IDS="12345678,87654321"    # CSV user id yang boleh pakai fitur kritikal
DATA_DIR="/opt/potion-runner"    # root app
LOG_DIR="/opt/potion-runner/logs"
BACKUP_DIR="/opt/potion-runner/backups"
HDD_MOUNT="/mnt/potion-data"     # target mount hdd
SERVICES_WHITELIST="potion-runner.service,cloudflared.service,n8n.service"
```

> Keamanan: `.env` permission 600, owner `dre:dre`.

---

## 7) Menu & Alur UX (ReplyKeyboard + Emoji)

**Menu Utama**
```
[ 📊 Status ]  [ 🧰 Kontrol ]
[ 📜 Logs ]    [ 💾 Backup ]
[ 🌐 Network ] [ 🔄 Update ]
[ ⚙️ Settings ]
```

**Contoh gaya bahasa**
- Saat proses: *"Oke, lagi aku cek dulu server kamu. Sabar sebentar ya ⚙️"*
- Setelah proses:
  - **Sukses**: *“Sudah siap nih! ✅ Info singkat: …”*
  - **Gagal**: *“Hmm, ada kendala nih ❌. Rangkuman error: … Coba lagi ya.”*

**Flows Ringkas**
- **📊 Status** → ringkas (CPU, RAM, Disk root + HDD, Suhu, Uptime, Services ringkasan) + tombol **Detail**.
- **🧰 Kontrol** → tombol per service (whitelist), `Restart`, `Start`, `Stop`; konfirmasi yes/no.
- **📜 Logs** → pilih sumber (app runtime, journalctl unit, dmesg ringkas), opsi `Tail 50`, `Cari "error"`, `Kirim file`.
- **💾 Backup** → `Backup now`, `Jadwal`, `Restore list` (pilih snapshot), `Verifikasi checksum`.
- **🌐 Network** → `IP info`, `Ping 1.1.1.1`, `Tailscale status`, `Speed quick`.
- **🔄 Update** → `Apt update+upgrade (safe)`, `Pip sync (from lock)`, `Pull repos`.
- **⚙️ Settings** → `Set jadwal backup`, `Toggle alert suhu/disk`, `Daftar admin`, `About`.

---

## 8) Perintah Bot (Command)

- `/start` – tampilkan menu & cek izin.
- `/help` – ringkas fitur & pengamanan.
- `/status` – ringkasan status cepat.
- `/logs runtime` – kirim tail `runtime.log`.
- `/backup` – jalankan backup segera.
- `/services` – daftar layanan whitelist + status.
- `/reboot` – reboot aman (konfirmasi).

> Semua aksi berat → kirim **pesan pending** *“tunggu sebentar ya…”*, **lalu** kirim **hasil akhir** (sukses/gagal).

---

## 9) Logging & Audit

- **runtime.log**: semua event aplikasi, level INFO+; **stream real‑time** (flush, no buffering) & tampil di terminal **dan** file.
- **actions.log**: siapa (user id) melakukan apa & kapan; simpan 90 hari.
- **Logrotate**: cap per file 10 MB, keep 10, compress.
- **journalctl**: simpan default (rotate otomatis oleh systemd).

**Contoh logrotate `/etc/logrotate.d/potion-runner`**
```
/opt/potion-runner/logs/*.log {
    daily
    rotate 10
    size 10M
    missingok
    compress
    delaycompress
    copytruncate
}
```

---

## 10) Backup & Restore (HDD 500 GB)

**Ruang HDD**: gunakan partisi `sdb4` (270 GB) atau `sdb5` (194 GB) → format ext4 dan mount ke `/mnt/potion-data`.

**Isi backup**
- `/opt/potion-runner/app` (kode & config non‑secret), `requirements.lock`.
- `/opt/potion-runner/logs`.
- File konfigurasi penting (unit systemd, fstab snippet) → `backups/manifests`.

**Jadwal**
- Harian 02:30 (systemd timer). Retensi 14 harian + 8 mingguan.

**Perintah (di belakang layar)**
- `rsync -a --delete` dari sumber ke snapshot `YYYY-MM-DD`.
- Buat `manifest.json` + `sha256sum`.

**Restore**
- Pilih snapshot → stop service → rsync balik → start service.

**Tambahan (opsional)**
- Sync ke cloud (rclone) mingguan.

---

## 11) Keandalan & Daya Tahan

- **systemd Service** (auto‑restart):
```
[Unit]
Description=Potion Runner Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
User=dre
WorkingDirectory=/opt/potion-runner
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/potion-runner/venv/bin/python -m app.bot
Restart=always
RestartSec=5
WatchdogSec=60
StartLimitIntervalSec=300
StartLimitBurst=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
- **systemd Timer** untuk backup harian & health ping.
- **Unattended‑upgrades** untuk security patch.
- **watchdog** opsional (kernel/software) jika perangkat sering hang.
- Laptop baterai = **UPS alami**; tetap aktifkan *safe shutdown* saat baterai kritis (ACPI default cukup).

---

## 12) Instalasi — Step by Step (awam)

> Tujuan: siapkan venv, mount HDD, jalankan bot sebagai service.

1) **Update sistem**  
- `sudo apt update && sudo apt upgrade -y`  
*Memperbarui daftar paket & memasang rilis terbaru yang aman.*

2) **Paket wajib**  
- `sudo apt install -y python3-venv python3-pip git rsync lm-sensors acl`  
*`venv/pip` untuk Python, `git` ambil kode, `rsync` untuk backup, `lm-sensors` baca suhu, `acl` izin file lebih fleksibel.*

3) **Siapkan HDD 500 GB**  
- Cek partisi: `lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID`  
- Pilih `sdb4` **atau** `sdb5`. Jika belum ext4 → format:  
  `sudo mkfs.ext4 -L POTIONDATA /dev/sdb4`  
  *Membuat sistem file ext4 bernama POTIONDATA.*
- Buat mount point & mount by UUID (lebih stabil):
  - `sudo mkdir -p /mnt/potion-data`
  - Dapatkan UUID: `sudo blkid /dev/sdb4`
  - Edit fstab: `sudo nano /etc/fstab` tambahkan baris:  
    `UUID=<UUIDSDB4> /mnt/potion-data ext4 defaults,noatime 0 2`
  - Mount ulang: `sudo mount -a` (cek error), lalu `df -h`.

4) **Buat folder aplikasi**  
```
sudo mkdir -p /opt/potion-runner/{app,logs,backups}
sudo chown -R dre:dre /opt/potion-runner
```
*`/opt` untuk aplikasi pihak ketiga; owner `dre` agar tidak jalan sebagai root.*

5) **Symlink ke HDD** (opsional tapi disarankan)  
```
mkdir -p /mnt/potion-data/potion-runner-{logs,backups}
ln -s /mnt/potion-data/potion-runner-logs /opt/potion-runner/logs
ln -s /mnt/potion-data/potion-runner-backups /opt/potion-runner/backups
```
*Log & backup mengalir ke HDD, SSD tetap lega.*

6) **Buat venv & install deps**  
```
python3 -m venv /opt/potion-runner/venv
/opt/potion-runner/venv/bin/pip install --upgrade pip
/opt/potion-runner/venv/bin/pip install "python-telegram-bot~=21.6" psutil python-dotenv aiofiles PyYAML
```
*`venv` membuat lingkungan Python terpisah. PTB v21 dipilih untuk kestabilan.*

7) **Siapkan kerangka kode**  
- Inisialisasi repo (clone atau `git init`).
- Tambah file sesuai **Struktur Folder** di atas.
- Buat `.env` dengan permission aman:
  `install -m 600 /dev/null /opt/potion-runner/.env && nano /opt/potion-runner/.env`.

8) **Konfigurasi logrotate**  
- Tambahkan file `/etc/logrotate.d/potion-runner` dengan isi pada bagian Logrotate di atas.

9) **Buat systemd unit**  
- Simpan file sebagai `/etc/systemd/system/potion-runner.service` (isi seperti di atas).  
- `sudo systemctl daemon-reload`  
- `sudo systemctl enable --now potion-runner`  
- Cek: `systemctl status potion-runner` (pastikan **active (running)**).

10) **Sensors** (opsional untuk suhu)
- Jalankan: `sudo sensors-detect` → pilih default aman.

11) **Uji alur**
- `/start` → tampil menu.
- Tekan **📊 Status** → harus keluar ringkasan.
- Coba **📜 Logs → Tail runtime** → kirim potongan log.
- Coba **💾 Backup → Backup now** → lihat snapshot di HDD.

---

## 13) Keamanan

- Bot token & admin IDs di `.env` (permission 600).
- Verifikasi **user id** pada setiap aksi sensitif (kontrol, reboot).
- Rate limit & flood control (PTB built‑in + debounce di handler).
- Validasi `systemctl` hanya pada **whitelist** service.
- Kontrol service membutuhkan rule sudoers tanpa password agar bot bisa eksekusi `systemctl` otomatis.
- Hindari mengeksekusi shell bebas; gunakan wrapper aman `run_cmd()` dengan timeout & exit code check.
- Log audit tindakan (user id, aksi, waktu, hasil).

---

## 14) Health Checks & Alerts

- **Health timer** 5 menit: kirim heartbeat (siluman) atau tulis file `last_ok`.
- **Alert** via Telegram jika:
  - CPU > 90% selama 5 menit.
  - RAM bebas < 500 MB.
  - Disk root/HDD > 90%.
  - Suhu CPU > ambang (mis. 85°C) selama 3 menit.
  - Service whitelisted **failed**.

> Agar tidak spam: gunakan jendela histeresis (kirim satu alert → tunggu recovery atau timeout minimal 15 menit).

---

## 15) Operasional Harian (cheats)

- Lihat status service: `systemctl status potion-runner`.
- Lihat log live: `journalctl -u potion-runner -f` **atau** `tail -f /opt/potion-runner/logs/runtime.log`.
- Restart bot: `sudo systemctl restart potion-runner`.
- Trigger backup manual: tombol bot **💾 Backup now**.

---

## 16) Rencana Uji (Test Plan)

- **Functional**: semua menu bekerja, tiap aksi kirim **pending → hasil**.
- **Permission**: user non‑admin tidak bisa aksi sensitif.
- **Failure**: matikan service dummy → pastikan alert & bisa `Restart`.
- **Power loss**: simulasi `echo b | sudo tee /proc/sysrq-trigger` (hati‑hati) → perangkat boot ulang → service **auto‑start** & bot online.
- **Disk full**: buat file dummy besar → cek alert & logrotate tetap berjalan.

---

## 17) Risiko & Mitigasi

- **Mati lampu** → laptop baterai menahan; systemd auto‑restart; filesystem ext4 journaling.
- **HDD tua** → SMART monitor (opsional), backup incremental & checksum; retensi snapshot.
- **Token bocor** → `.env` 600; hindari print token di log; rotate token bila perlu.
- **Spam alert** → rate‑limit & hysteresis.

---

## 18) Roadmap (Nice‑to‑Have)

- Panel read‑only (Netdata) dengan link dari bot.
- Perintah custom script (templated & whitelisted).
- Integrasi Cloud backup (rclone/B2/Drive).
- Multi‑agent: tambahkan worker untuk tugas berat (queue Redis lokal).
- Export Prometheus (metrics endpoint) jika kelak dipakai Grafana.

---

## 19) Acceptance Criteria (agar “Codex” tidak setengah‑setengah)

1. **Struktur folder** persis seperti di PRD, file inti ada.
2. **Menu ReplyKeyboard** tampil sesuai desain + emoji.
3. **Pesan pending** untuk aksi >1s, lalu **sukses/gagal** dengan ringkasan.
4. **runtime.log** mencatat real‑time, dapat di‑tail dari bot.
5. **Backup harian** via systemd timer → snapshot muncul di HDD.
6. **Kontrol service** hanya pada whitelist, semua aksi tercatat di `actions.log`.
7. **Alert** untuk CPU/RAM/Disk/Suhu/Service fail dengan anti‑spam.
8. **Install script**/README menjelaskan step by step untuk pemula, sesuai bagian **Instalasi** di dokumen ini.

---

## 20) Contoh ReplyKeyboard (JSON sketsa)

```json
[
  ["📊 Status", "🧰 Kontrol"],
  ["📜 Logs", "💾 Backup"],
  ["🌐 Network", "🔄 Update"],
  ["⚙️ Settings"]
]
```

---

## 21) Contoh Teks Template

- `PROCESSING`: "Oke, lagi aku cek dulu server kamu. Sabar sebentar ya ⚙️"
- `DONE_OK`: "Beres! ✅ Ringkasan: {summary}"
- `DONE_FAIL`: "Kenapa ya... ❌ Ada error: {error}. Coba ulang sebentar lagi, aku standby kok."
- `CONFIRM`: "Yakin mau {action}? Balas *YA* kalau sudah mantap."

---

### Catatan Akhir
- PRD ini **cukup detail** agar implementasi langsung jalan di Kubuntu 24.04, ringan, aman, dan mudah dirawat.
- Fokuskan dulu fitur **Monitoring, Kontrol, Logs, Backup**. Tambahan lain bisa menyusul tanpa bongkar arsitektur.
