# Rencana Pengembangan Jangka Panjang: Server Potion

Dokumen ini menguraikan visi, rencana pemeliharaan, dan roadmap pengembangan untuk Server Potion dan Potion Runner Bot. Tujuannya adalah untuk memaksimalkan potensi server, terutama dengan memanfaatkan kapasitas HDD yang tersedia.

## Visi Jangka Panjang

Menjadikan Server Potion sebagai pusat digital pribadi yang andal dan serbaguna untuk kebutuhan backup, media, dan otomatisasi tugas-tugas rutin, yang semuanya dapat dikelola dengan mudah melalui antarmuka Potion Runner Bot yang intuitif dan responsif.

## Pemanfaatan HDD (`/mnt/dre`)

HDD berkapasitas 500GB adalah aset utama yang belum dimanfaatkan sepenuhnya. Berikut adalah beberapa rencana untuk menggunakannya:

1.  **Pusat Backup Terpusat:**
    *   **Target:** Menjadikan HDD sebagai lokasi utama untuk mencadangkan data penting dari berbagai perangkat (laptop, PC, bahkan ponsel).
    *   **Implementasi:** Menggunakan alat seperti `rsync` untuk backup file sederhana atau `restic` dan `borg` untuk backup yang lebih canggih (terenkripsi, terduplikasi, dan incremental). Proses ini akan diotomatisasi dan dapat dipicu serta dipantau melalui Potion Runner Bot.

2.  **Server Media Pribadi:**
    *   **Target:** Menyimpan koleksi film, musik, dan foto di HDD dan mengaksesnya dari perangkat apa pun di jaringan.
    *   **Implementasi:** Memasang dan mengonfigurasi layanan media streaming seperti **Jellyfin** atau **Plex** menggunakan Docker. Bot akan dilengkapi fitur untuk memindai ulang perpustakaan media atau memeriksa status server.

3.  **Platform Download Otomatis:**
    *   **Target:** Mengelola unduhan file besar langsung ke server tanpa perlu menyalakan PC/laptop terus-menerus.
    *   **Implementasi:** Menjalankan aplikasi seperti **qBittorrent (dengan web UI)** atau **JDownloader** di dalam kontainer Docker, dengan direktori unduhan diarahkan ke HDD. Bot bisa digunakan untuk memantau kemajuan unduhan atau menambahkan file torrent baru.

## Roadmap Pengembangan Potion Runner Bot

Bot akan terus dikembangkan untuk mendukung fungsionalitas server yang baru:

### Fase 1: Fondasi dan Perbaikan (Prioritas Saat Ini)

*   [x] **Perbaikan Bug:** Menyelesaikan masalah pada perintah `/speed` yang macet.
*   [x] **Peningkatan UI/UX:** Mengimplementasikan pesan yang lebih kasual, emoji, dan umpan balik instan pada setiap interaksi menu.
*   **Konfigurasi Dasar HDD:** Memastikan HDD terpasang (`mount`) secara permanen dan dapat diakses dengan benar oleh sistem.
*   **Monitoring HDD:** Menambahkan fitur pada menu "📊 Status" untuk menampilkan penggunaan ruang disk pada partisi `/mnt/dre`.

### Fase 2: Backup dan Media

*   **Integrasi Backup:** Membuat menu baru "🛡️ Backup Lanjutan" di bot untuk mengelola tugas-tugas `restic` atau `rsync`. Fitur akan mencakup: memulai backup, melihat daftar snapshot, dan memulihkan file.
*   **Instalasi Media Server:** Memasang Jellyfin atau Plex via Docker.
*   **Kontrol Media Server:** Menambahkan perintah di dalam menu "🐳 Docker" untuk memulai ulang atau memeriksa status kontainer media server.

### Fase 3: Otomatisasi dan Lanjutan

*   **Integrasi Klien Download:** Menambahkan kontrol dasar untuk qBittorrent atau JDownloader melalui bot.
*   **Notifikasi Cerdas:** Mengembangkan sistem notifikasi yang lebih proaktif. Contoh:
    *   Memberi tahu admin jika backup gagal.
    *   Memberi tahu saat unduhan selesai.
    *   Memberi peringatan jika kesehatan HDD (berdasarkan S.M.A.R.T.) menurun.
*   **Keamanan:** Mengkaji ulang dan memperkuat keamanan, terutama pada fitur `/run` yang mengeksekusi perintah shell langsung.

## Pemeliharaan Rutin

*   **Pembaruan Sistem:** Bot akan memiliki fitur untuk menjadwalkan atau menjalankan `sudo apt update && sudo apt upgrade -y` secara berkala dan melaporkan hasilnya.
*   **Pemeriksaan Kesehatan HDD:** Mengintegrasikan `smartmontools` untuk memantau status S.M.A.R.T. HDD dan mengirimkan peringatan melalui bot jika terdeteksi anomali.
*   **Pembersihan Log:** Otomatisasi pembersihan file log lama untuk mencegah disk penuh.

## Menuju Smart Server: Fitur Cerdas (Fase 4)

Fase ini bertujuan untuk mengubah bot dari alat reaktif menjadi asisten server yang proaktif dan cerdas.

### 1. Pemantauan Proaktif & Prediktif

*   **Analisis Tren Penggunaan:** Bot akan menyimpan data historis (CPU, RAM, disk) untuk mendeteksi anomali. Misalnya, jika penggunaan RAM terus meningkat selama beberapa hari, bot akan memberi tahu admin tentang kemungkinan *memory leak* sebelum menjadi masalah.
*   **Notifikasi Keamanan Cerdas:**
    *   **Deteksi Upaya Login Gagal:** Memantau log otentikasi (`/var/log/auth.log`) dan mengirimkan peringatan jika ada terlalu banyak upaya login SSH yang gagal dari satu alamat IP.
    *   **Peringatan `sudo`:** Memberi notifikasi setiap kali perintah `sudo` digunakan di luar bot, memberikan visibilitas penuh terhadap aktivitas admin di server.
*   **Prediksi Kegagalan Disk:** Tidak hanya membaca status S.M.A.R.T. saat ini, tetapi juga menganalisis atribut-atribut kritis (seperti *Reallocated Sectors Count*) dari waktu ke waktu untuk memprediksi potensi kegagalan HDD.

### 2. Otomatisasi Cerdas & Mandiri

*   **Manajemen Ruang Disk Otomatis:**
    *   **Pembersihan Cerdas:** Bot akan secara otomatis menghapus file-file yang tidak lagi relevan, seperti log lama, *cache* paket (`apt`), atau unduhan yang sudah selesai dan dipindahkan ke perpustakaan media.
    *   **Rotasi Backup:** Menerapkan kebijakan rotasi backup otomatis (misalnya, simpan backup harian selama 7 hari, mingguan selama 4 minggu, dan bulanan selama 6 bulan) untuk menghemat ruang.
*   **Penyembuhan Diri (*Self-Healing*):**
    *   **Restart Layanan Otomatis:** Jika `health_check_job` mendeteksi layanan sistemd yang gagal, bot akan mencoba me-restart layanan tersebut satu atau dua kali. Jika tetap gagal, barulah notifikasi dikirim ke admin.
*   **Integrasi Alur Kerja:**
    *   **Otomatisasi Media:** Setelah klien unduhan (qBittorrent/JDownloader) menyelesaikan sebuah file, bot akan secara otomatis memicu pemindaian perpustakaan di Jellyfin/Plex.

### 3. Diagnostik Berbantuan AI

*   **Perintah `/diagnose`:**
    *   **Target:** Membuat perintah yang dapat membantu admin mendiagnosis masalah dengan cepat.
    *   **Implementasi (Konsep):** Saat admin menjalankan `/diagnose <service>`, bot akan:
        1.  Mengambil log terbaru dari `journalctl` untuk layanan tersebut.
        2.  Menganalisis log untuk mencari kata kunci error yang umum (`failed`, `error`, `timeout`).
        3.  Menggunakan model bahasa (bisa melalui API eksternal atau model lokal yang lebih kecil) untuk merangkum masalah dan memberikan saran perbaikan berdasarkan pesan error yang ditemukan. Contoh: "Aku melihat ada error 'permission denied' di log Nginx. Coba periksa izin pada direktori `/var/www/html`."
