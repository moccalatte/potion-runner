# Potion Runner Bot 🧪

Bot Telegram async berbasis `python-telegram-bot` v21 untuk memantau dan mengontrol node MCP/RAG pada **Server Potion** (setara VPS i5-4210u, RAM 8GB, SSD 256GB, HDD 500GB). Proyek ini memprioritaskan pengalaman pengguna yang ramah, logging real-time, backup otomatis, serta watchdog alert.

## ✨ Fitur Utama
- **📊 Monitoring Cepat**: CPU, RAM, disk (root & HDD), uptime, suhu, status layanan.
- **🔐 Kontrol Aman**: Start/stop/restart service systemd, update terjadwal, audit log.
- **📜 Manajemen Log**: Tail runtime, grep error, kirim file log, akses journalctl.
- **🐳 Manajemen Docker**: List, stop, restart, dan lihat log kontainer Docker langsung dari bot.
- **💾 Backup Rsync**: Snapshot harian ke HDD (`/mnt/dre`), verifikasi checksum.
- **🌐 Network Tools**: Info IP, ping, status Tailscale, speed test.
- **⚠️ Alert & Watchdog**: Deteksi anomali resource (CPU/RAM/Disk/Suhu) dan service down.
- **⚙️ Pengaturan Dinamis**: Jadwal backup, threshold alert, dan whitelist service bisa diubah dari bot.

---

## 🚀 Instalasi (untuk Ubuntu 24.04 LTS)

Panduan ini dirancang untuk pemula dan mencakup semua langkah yang diperlukan untuk menjalankan bot secara stabil. Semua file aplikasi dan data akan disimpan di `/mnt/dre/potion-runner`.

### 🛠️ Langkah 1: Persiapan Awal

1.  **🔄 Update Sistem**: Pastikan server Anda menggunakan paket terbaru.
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **📦 Install Dependensi**: Pasang semua paket yang dibutuhkan oleh bot.
    ```bash
    sudo apt install -y python3-venv python3-pip git rsync
    # Opsional (tapi direkomendasikan):
    sudo apt install -y lm-sensors smartmontools tailscale speedtest-cli
    ```

### 💾 Langkah 2: Siapkan HDD (`/mnt/dre`)

Aplikasi ini dirancang untuk berjalan sepenuhnya dari HDD yang di-mount di `/mnt/dre`.

1.  **🔍 Cek Partisi**: Lihat daftar partisi untuk menemukan HDD target. Partisi yang disarankan adalah `/dev/sdb1`.
    ```bash
    lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID
    ```

2.  **🧹 Format (Jika Perlu)**: Jika `/dev/sdb1` belum diformat, format sebagai `ext4`. **Peringatan: Ini akan menghapus semua data di partisi tersebut.**
    ```bash
    sudo mkfs.ext4 -L POTIONDATA /dev/sdb1
    ```

3.  **⚙️ Mount Otomatis**: Konfigurasikan `fstab` agar HDD termount saat boot.
    *   Dapatkan UUID partisi: `sudo blkid /dev/sdb1`
    *   Edit `/etc/fstab`: `sudo nano /etc/fstab`
    *   Tambahkan baris berikut (ganti `<UUID_ANDA>` dengan UUID dari langkah sebelumnya):
        ```
        UUID=<UUID_ANDA> /mnt/dre ext4 defaults,noatime 0 2
        ```
    *   Mount dan verifikasi:
        ```bash
        sudo mkdir -p /mnt/dre
        sudo mount -a
        df -h # Pastikan /mnt/dre sudah muncul
        ```

### 🤖 Langkah 3: Install Potion Runner Bot

Gunakan skrip instalasi yang sudah disediakan untuk otomatisasi.

1.  **📥 Clone Repositori**:
    ```bash
    cd /mnt/dre
    git clone https://github.com/moccalatte/potion-runner.git
    cd potion-runner
    ```

2.  **🏃 Jalankan Skrip Instalasi**:
    *   Skrip ini akan menginstal semua komponen ke dalam `/mnt/dre/potion-runner`.
    *   Pastikan Anda menjalankannya dari dalam direktori repositori.
    ```bash
    # Jalankan sebagai user biasa (bukan root)
    ./scripts/install.sh
    ```
    Skrip ini akan:
    *   Membuat direktori yang diperlukan (`logs`, `backups`, dll.).
    *   Mengatur kepemilikan file (`chown`) agar sesuai dengan user Anda.
    *   Membuat virtual environment Python dan menginstall dependensi.
    *   Menyalin file `.env.example` ke `.env`.
    *   Menginstall dan mengonfigurasi service `systemd` dan `logrotate`.
    *   Mengaktifkan dan menjalankan service bot.

### 📝 Langkah 4: Konfigurasi Bot

1.  **✏️ Edit File `.env`**: Buka file konfigurasi dan isi nilainya.
    ```bash
    nano /mnt/dre/potion-runner/.env
    ```
    *   `BOT_TOKEN`: Token bot dari BotFather Telegram.
    *   `ADMIN_IDS`: ID user Telegram Anda (bisa lebih dari satu, pisahkan dengan koma). Dapatkan dari bot seperti `@userinfobot`.

2.  **🔄 Restart Bot**: Terapkan konfigurasi baru dengan me-restart service.
    ```bash
    sudo systemctl restart potion-runner.service
    ```

### 🔐 Langkah 5: Konfigurasi Izin `sudo` (Penting!)

Agar bot bisa me-restart service lain, Anda perlu memberikan izin `sudo` tanpa password.

1.  **✍️ Buat File Sudoers**:
    ```bash
    sudo nano /etc/sudoers.d/potion-runner
    ```

2.  **📜 Tambahkan Aturan**:
    *   Ganti `your_user` dengan user yang menjalankan bot (kemungkinan besar user Anda saat ini).
    *   Tambahkan semua service yang ingin Anda kontrol dari bot.
    ```
    your_user ALL=(root) NOPASSWD: /usr/bin/systemctl start SERVICE_1, /usr/bin/systemctl stop SERVICE_1, /usr/bin/systemctl restart SERVICE_1
    ```
    **Contoh**:
    ```
    dre ALL=(root) NOPASSWD: /usr/bin/systemctl start n8n.service, /usr/bin/systemctl stop n8n.service, /usr/bin/systemctl restart n8n.service
    dre ALL=(root) NOPASSWD: /usr/bin/docker ps, /usr/bin/docker stop *, /usr/bin/docker restart *, /usr/bin/docker logs *
    ```

3.  **🔒 Setel Izin File**:
    ```bash
    sudo chmod 440 /etc/sudoers.d/potion-runner
    ```

### ✅ Langkah 6: Verifikasi

1.  **🩺 Cek Status Service**:
    ```bash
    systemctl status potion-runner.service
    # Harusnya menampilkan "active (running)"
    ```

2.  **📄 Lihat Log**:
    ```bash
    journalctl -u potion-runner -f
    ```

3.  **📱 Buka Bot Telegram**: Kirim `/start` ke bot Anda. Jika semua berjalan lancar, menu utama akan muncul.

---

## 📂 Struktur Direktori

Semua file, termasuk kode, data, log, dan backup, berada di: `/mnt/dre/potion-runner/`

## ☀️ Operasional Harian
- **🔄 Restart Bot**: `sudo systemctl restart potion-runner`
- **👀 Lihat Log**: `journalctl -u potion-runner -f` atau `tail -f /mnt/dre/potion-runner/logs/runtime.log`
- **⬆️ Update Bot**:
  ```bash
  cd /mnt/dre/potion-runner
  git pull
  sudo systemctl restart potion-runner
  ```

Selamat menggunakan Potion Runner Bot! 🎉
