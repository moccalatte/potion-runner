# Potion Runner Bot

Bot Telegram async berbasis `python-telegram-bot` v21 untuk memantau dan mengontrol node MCP/RAG pada **Server Potion** (setara VPS i5-4210u, RAM 8GB, SSD 256GB, HDD 500GB). Proyek ini memprioritaskan pengalaman pengguna yang ramah, logging real-time, backup otomatis, serta watchdog alert.

## Fitur Utama
- **Monitoring Cepat**: CPU, RAM, disk (root & HDD), uptime, suhu, status layanan.
- **Kontrol Aman**: Start/stop/restart service systemd, update terjadwal, audit log.
- **Manajemen Log**: Tail runtime, grep error, kirim file log, akses journalctl.
- **Backup Rsync**: Snapshot harian ke HDD (`/mnt/dre`), verifikasi checksum.
- **Network Tools**: Info IP, ping, status Tailscale, speed test.
- **Alert & Watchdog**: Deteksi anomali resource (CPU/RAM/Disk/Suhu) dan service down.
- **Pengaturan Dinamis**: Jadwal backup, threshold alert, dan whitelist service bisa diubah dari bot.

---

## Instalasi (untuk Ubuntu 24.04 LTS)

Panduan ini dirancang untuk pemula dan mencakup semua langkah yang diperlukan untuk menjalankan bot secara stabil.

### Langkah 1: Persiapan Awal

1.  **Update Sistem**: Pastikan server Anda menggunakan paket terbaru.
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Install Dependensi**: Pasang semua paket yang dibutuhkan oleh bot.
    ```bash
    sudo apt install -y python3-venv python3-pip git rsync
    # Opsional (tapi direkomendasikan):
    sudo apt install -y lm-sensors smartmontools tailscale speedtest-cli
    ```

### Langkah 2: Siapkan HDD untuk Data Aplikasi

Semua data (log, backup, config) akan disimpan di `/mnt/dre` untuk memisahkan data dari sistem operasi dan kode aplikasi.

1.  **Cek Partisi**: Lihat daftar partisi untuk menemukan HDD target.
    ```bash
    lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID
    ```

2.  **Format (Jika Perlu)**: Jika HDD belum diformat, format sebagai `ext4`. **Peringatan: Ini akan menghapus semua data di partisi tersebut.**
    ```bash
    sudo mkfs.ext4 -L POTIONDATA /dev/sdXN # Ganti /dev/sdXN dengan partisi Anda
    ```

3.  **Mount Otomatis**: Konfigurasikan `fstab` agar HDD termount saat boot.
    *   Dapatkan UUID partisi: `sudo blkid /dev/sdXN`
    *   Edit `/etc/fstab`: `sudo nano /etc/fstab`
    *   Tambahkan baris berikut (ganti `<UUID_HDD_ANDA>` dengan UUID dari langkah sebelumnya):
        ```
        UUID=<UUID_HDD_ANDA> /mnt/dre ext4 defaults,noatime 0 2
        ```
    *   Mount dan verifikasi:
        ```bash
        sudo mkdir -p /mnt/dre
        sudo mount -a
        df -h # Pastikan /mnt/dre sudah muncul
        ```

### Langkah 3: Install Potion Runner Bot

Gunakan skrip instalasi yang sudah disediakan untuk otomatisasi.

1.  **Clone Repositori**:
    ```bash
    git clone https://github.com/username/potion-runner.git # Ganti dengan URL repo Anda
    cd potion-runner
    ```

2.  **Jalankan Skrip Instalasi**:
    *   `SERVICE_USER` adalah user yang akan menjalankan bot (disarankan bukan `root`).
    *   `APP_DIR` adalah lokasi kode aplikasi (default: `/opt/potion-runner`).
    *   `DATA_DIR` adalah lokasi data (default: `/mnt/dre/potion-runner`).
    ```bash
    # Jalankan sebagai user biasa (bukan root)
    ./scripts/install.sh
    ```
    Skrip ini akan:
    *   Menyalin kode aplikasi ke `/opt/potion-runner`.
    *   Membuat direktori data di `/mnt/dre/potion-runner`.
    *   Mengatur kepemilikan file (`chown`) agar sesuai dengan `SERVICE_USER`.
    *   Membuat virtual environment Python dan menginstall dependensi.
    *   Menyalin file `.env.example` ke `/mnt/dre/potion-runner/.env`.
    *   Menginstall service `systemd` dan `logrotate` untuk otomatisasi.
    *   Mengaktifkan dan menjalankan service bot.

### Langkah 4: Konfigurasi Bot

1.  **Edit File `.env`**: Buka file konfigurasi dan isi nilainya.
    ```bash
    nano /mnt/dre/potion-runner/.env
    ```
    *   `BOT_TOKEN`: Token bot dari BotFather Telegram.
    *   `ADMIN_IDS`: ID user Telegram Anda (bisa lebih dari satu, pisahkan dengan koma). Dapatkan dari bot seperti `@userinfobot`.

2.  **Restart Bot**: Terapkan konfigurasi baru dengan me-restart service.
    ```bash
    sudo systemctl restart potion-runner.service
    ```

### Langkah 5: Konfigurasi Izin `sudo` (Penting!)

Agar bot bisa me-restart service lain, Anda perlu memberikan izin `sudo` tanpa password untuk perintah tertentu.

1.  **Buat File Sudoers**:
    ```bash
    sudo nano /etc/sudoers.d/potion-runner
    ```

2.  **Tambahkan Aturan**:
    *   Ganti `your_user` dengan user yang menjalankan bot (`SERVICE_USER`).
    *   Tambahkan semua service yang ingin Anda kontrol dari bot ke dalam daftar.
    ```
    your_user ALL=(root) NOPASSWD: /usr/bin/systemctl start SERVICE_1, /usr/bin/systemctl stop SERVICE_1, /usr/bin/systemctl restart SERVICE_1, /usr/bin/systemctl start SERVICE_2, /usr/bin/systemctl stop SERVICE_2, /usr/bin/systemctl restart SERVICE_2
    ```
    **Contoh**:
    ```
    dre ALL=(root) NOPASSWD: /usr/bin/systemctl start n8n.service, /usr/bin/systemctl stop n8n.service, /usr/bin/systemctl restart n8n.service
    ```

3.  **Setel Izin File**:
    ```bash
    sudo chmod 440 /etc/sudoers.d/potion-runner
    ```

### Langkah 6: Verifikasi

1.  **Cek Status Service**:
    ```bash
    systemctl status potion-runner.service
    # Harusnya menampilkan "active (running)"
    ```

2.  **Lihat Log**:
    ```bash
    journalctl -u potion-runner -f
    ```

3.  **Buka Bot Telegram**: Kirim `/start` ke bot Anda. Jika semua berjalan lancar, menu utama akan muncul.

---

## Struktur Direktori

*   **Kode Aplikasi**: `/opt/potion-runner/`
*   **Data, Log, & Backup**: `/mnt/dre/potion-runner/`

## Operasional Harian
- **Restart Bot**: `sudo systemctl restart potion-runner`
- **Lihat Log**: `journalctl -u potion-runner -f`
- **Update Bot**:
  ```bash
  cd /opt/potion-runner
  git pull
  sudo systemctl restart potion-runner
  ```

Selamat menggunakan Potion Runner Bot! 🧪
