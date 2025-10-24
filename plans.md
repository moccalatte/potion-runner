# Rencana Pengembangan: "Project Cockpit"

Dokumen ini adalah cetak biru untuk mengubah Potion Runner Bot menjadi **"Cockpit"**, sebuah panel kontrol terpusat yang intuitif dan kuat untuk mengelola semua aspek Server Potion. Setiap fitur dirancang sebagai instrumen, tombol, atau layar informasi di dalam kokpit virtual ini.

---

## Visi Utama: Server sebagai Pesawat Luar Angkasa

Kita akan memperlakukan server bukan lagi sebagai mesin statis, tetapi sebagai "pesawat" pribadi yang kita piloti. Bot adalah kokpit kita. Ini berarti setiap interaksi harus:
*   **Informatif:** Memberikan data yang jelas dan relevan dengan cepat.
*   **Responsif:** Memberikan kendali instan atas semua sistem kritis.
*   **Cerdas:** Membantu pilot (admin) membuat keputusan yang lebih baik dan mengotomatiskan tugas-tugas rutin.

---

## Struktur Panel Kontrol "Cockpit"

Menu utama bot akan menjadi *dashboard* untuk mengakses panel-panel berikut:

### 🚀 Panel Utama (Dashboard Utama)

Tampilan awal yang menunjukkan status paling kritis secara sekilas (misalnya, status sistem OK/Peringatan, penggunaan disk, beban CPU) dan menyediakan akses ke panel-panel lainnya.

### ⚙️ Panel Mesin (Engine Room) - *Kesehatan & Performa Inti*

*   **Layar Status Sistem:**
    *   **Metrik Real-time:** Tampilan detail CPU (beban, suhu), RAM (terpakai, *cache*, tersedia), dan penggunaan *swap*.
    *   **Kesehatan Disk:** Penggunaan ruang disk untuk partisi `/` dan `/mnt/dre`. Integrasi `smartmontools` untuk menampilkan status kesehatan S.M.A.R.T.
    *   **Uptime & Waktu Boot:** Informasi uptime server.
*   **Kontrol Layanan (`systemctl`):**
    *   Daftar layanan yang dipantau dengan indikator status (aktif/tidak aktif/gagal).
    *   Tombol cepat untuk `start`, `stop`, `restart` layanan dari daftar.
    *   Akses cepat untuk melihat log `journalctl` dari layanan yang gagal.
*   **Manajemen Proses:**
    *   Tampilkan daftar proses yang paling banyak memakan CPU/RAM (mirip `htop`).
    *   Fungsi untuk "membunuh" (*kill*) proses berdasarkan PID.

### 📦 Panel Kargo (Cargo Bay) - *Aplikasi & Data*

*   **Kontrol Kontainer 🐳 (Docker):**
    *   Daftar kontainer dengan status, port, dan penggunaan sumber daya.
    *   Kontrol penuh: `start`, `stop`, `restart`, `pause`, `unpause`.
    *   Lihat log kontainer secara *real-time*.
    *   Informasi volume dan jaringan yang terhubung.
*   **Manajemen Penyimpanan 🗃️:**
    *   **File Browser:** Navigasi direktori di `/mnt/dre`, lihat ukuran file/folder, hapus, dan pindahkan.
    *   **Transfer File:** Unggah/unduh file antara Telegram dan server.
    *   **Analisis Penggunaan Disk:** Visualisasi penggunaan disk untuk melihat folder mana yang paling banyak memakan ruang.
*   **Sistem Backup & Pemulihan 💾:**
    *   **Backup (Restic/Borg):** Jalankan backup manual, lihat daftar *snapshot*, dan verifikasi integritas data.
    *   **Pemulihan Bencana:** Fitur untuk memulihkan file atau direktori tertentu dari *snapshot* backup.

### 📡 Panel Navigasi & Komunikasi (Navigation & Comms) - *Jaringan & Keamanan*

*   **Layar Jaringan:**
    *   **Status Konektivitas:** Hasil `ping` ke target-target penting (misalnya, gateway, 8.8.8.8).
    *   **Tes Kecepatan Internet:** Perintah `/speed` yang andal.
    *   **Lalu Lintas Jaringan:** Tampilkan penggunaan *bandwidth* saat ini (mirip `nload`).
*   **Sistem Keamanan:**
    *   **Firewall (`ufw`/`iptables`):** Lihat aturan firewall yang aktif, buka/tutup port sementara.
    *   **Log Keamanan:** Pantau `/var/log/auth.log` untuk upaya login yang gagal dan tampilkan peringatan.
    *   **Integrasi Fail2Ban:** Lihat daftar IP yang diblokir dan buka blokir.
*   **Manajemen VPN (Tailscale):**
    *   Daftar perangkat di jaringan Tailnet.
    *   Status konektivitas setiap perangkat.

### 🛠️ Panel Pengaturan & Log Penerbangan (Settings & Flight Recorder)

*   **Pengaturan Bot:**
    *   **Manajemen Admin:** Tambah/hapus ID admin.
    *   **Kustomisasi Notifikasi:** Atur ambang batas untuk peringatan (CPU > 90%, disk > 85%).
    *   **Jadwal Otomatis:** Atur jadwal untuk backup otomatis dan pembersihan.
*   **Pencatatan & Audit (Log):**
    *   Akses mudah ke log sistem, log aplikasi, dan log bot itu sendiri.
    *   Fitur pencarian di dalam log.

### ✨ Co-Pilot Cerdas (Fitur Otomatis & Proaktif)

Ini bukan menu, melainkan serangkaian fitur "di balik layar" yang membuat kokpit ini cerdas.

*   **Peringatan Prediktif:** Analisis tren penggunaan sumber daya untuk memperingatkan potensi masalah (*memory leak*, disk penuh) sebelum terjadi.
*   **Penyembuhan Diri (*Self-Healing*):** Jika layanan penting gagal, bot akan mencoba me-restartnya secara otomatis. Jika gagal lagi, barulah pilot diberi tahu.
*   **Laporan Misi Mingguan:** Ringkasan otomatis setiap minggu tentang kesehatan server, backup yang berhasil, dan anomali yang terdeteksi.
*   **Asisten Diagnostik `/diagnose`:** Membantu pilot menganalisis log error dan memberikan saran perbaikan.
