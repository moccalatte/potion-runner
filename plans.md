# Rencana Aksi Strategis: Potion Server

Dokumen ini adalah panduan utama untuk pemeliharaan, perbaikan, dan evolusi Potion Server. Tujuannya adalah mengubah server ini menjadi platform *self-hosting* yang andal, aman, dan cerdas.

---

## 1. Masalah Mendesak & Perbaikan Teknis

Daftar ini berisi masalah, anomali, dan utang teknis yang harus segera ditangani untuk meningkatkan stabilitas dan kualitas kode.

*   **Penyempurnaan Penanganan Error Global:**
    *   **Masalah:** Saat ini, `error_handler` di `app/bot.py` hanya mencatat error ke log. Admin tidak mendapatkan notifikasi langsung jika bot mengalami *crash* atau gagal memproses permintaan.
    *   **Solusi:** Modifikasi `error_handler` untuk mengirim pesan peringatan ke semua `ADMIN_IDS` setiap kali ada error tak terduga, lengkap dengan *traceback* singkat.

*   **Struktur Konfigurasi Terpusat:**
    *   **Masalah:** Banyak string teks, emoji, dan parameter (seperti jumlah baris log untuk diambil) tersebar di dalam kode (*hardcoded*). Ini menyulitkan kustomisasi.
    *   **Solusi:** Pindahkan semua konfigurasi yang dapat diubah pengguna (pesan bot, emoji, pengaturan fungsional) ke dalam satu file konfigurasi terpusat (misalnya, `config.toml` atau `settings.py` yang lebih terstruktur) agar mudah dimodifikasi.

*   **Peningkatan Cakupan Pengujian (*Test Coverage*):**
    *   **Masalah:** Belum ada jaminan bahwa semua fungsionalitas kritis (terutama yang menjalankan perintah shell seperti `systemctl` dan `apt`) teruji dengan baik.
    *   **Solusi:** Implementasikan `pytest-cov` untuk mengukur cakupan pengujian. Tulis tes tambahan untuk setiap fungsi di `app/services` dan `app/handlers` yang belum teruji, terutama untuk skenario sukses dan gagal.

*   **Mekanisme Umpan Balik yang Konsisten:**
    *   **Masalah:** Pesan "sedang diproses" telah ditambahkan secara manual ke beberapa *handler*, tetapi belum konsisten.
    *   **Solusi:** Buat *decorator* Python (`@send_processing_message`) yang bisa diterapkan pada fungsi *handler* mana pun untuk secara otomatis mengirim pesan "sedang diproses" di awal dan menghapusnya di akhir.

---

## 2. Roadmap Fitur & Peningkatan Server

Daftar ide dan fitur baru untuk memaksimalkan kegunaan server, diurutkan berdasarkan area fungsional.

### Area Inti: Keamanan & Pemeliharaan

*   **Menu 🛡️ Keamanan:**
    *   **Pemantau Log Otentikasi:** Tampilkan ringkasan upaya login SSH (berhasil dan gagal) dari `/var/log/auth.log`.
    *   **Manajemen `fail2ban`:** Integrasikan perintah untuk melihat status, daftar IP yang diblokir, dan membuka blokir IP langsung dari bot.
    *   **Pindai Port Terbuka:** Jalankan `nmap` atau `ss` dari bot untuk memeriksa port mana yang terbuka ke internet.

*   **Otomatisasi Pemeliharaan Cerdas:**
    *   **Pembersihan Otomatis:** Jadwalkan tugas pembersihan mingguan untuk menghapus *cache* `apt`, *thumbnail* lama, dan log yang sudah dirotasi.
    *   **Rotasi & Arsip Backup:** Terapkan kebijakan rotasi backup otomatis (harian, mingguan, bulanan) dan pindahkan backup bulanan yang sangat lama ke penyimpanan arsip (jika ada).
    *   ***Self-Healing* untuk Layanan:** Jika layanan penting (misalnya, `nginx` atau `docker.service`) mati, bot akan mencoba me-restartnya secara otomatis sebelum memberi tahu admin.

### Area Produktivitas: Pemanfaatan HDD

*   **Menu 🗃️ Manajemen File:**
    *   **File Browser Sederhana:** Fitur untuk melihat daftar file dan direktori di `/mnt/dre`, menghitung ukuran folder, dan menghapus file/folder.
    *   **Transfer File:** Unggah file dari Telegram langsung ke server, atau sebaliknya, minta bot mengirimkan file dari server.

*   **Menu 🚀 Pusat Unduhan (*Download Hub*):**
    *   **Integrasi qBittorrent/Transmission:** Tambahkan, jeda, lanjutkan, dan lihat status unduhan *torrent* melalui bot. Dapatkan notifikasi saat unduhan selesai.
    *   **Manajemen `yt-dlp`:** Perintah untuk mengunduh video dari YouTube dan platform lain langsung ke server.

*   **Menu 🎬 Server Media:**
    *   **Integrasi Jellyfin/Plex:**
        *   Lihat item yang baru ditambahkan.
        *   Mulai pemindaian perpustakaan secara manual.
        *   Dapatkan statistik penggunaan (misalnya, siapa yang sedang menonton apa).
    *   **Otomatisasi Perpustakaan:** Secara otomatis memicu pemindaian perpustakaan media setelah unduhan baru selesai di Pusat Unduhan.

### Area Jaringan & Konektivitas

*   **Menu 🌐 Jaringan (Lanjutan):**
    *   **Manajemen Tailscale:**
        *   Lihat daftar perangkat (*peers*) di jaringan Tailnet.
        *   Aktifkan/nonaktifkan koneksi Tailscale.
    *   **Visualisasi Lalu Lintas Jaringan:** Gunakan `nload` atau `iftop` untuk menghasilkan gambar atau teks ringkasan tentang penggunaan *bandwidth* saat ini.
    *   **Bookmark Cepat:** Simpan daftar alamat IP/domain yang sering di-*ping* agar bisa diakses dengan cepat.

### Fitur "Smart" & Eksperimental

*   **Asisten Diagnostik `/diagnose`:**
    *   **Fungsi:** Ketika sebuah layanan gagal, admin bisa menjalankan `/diagnose <nama_layanan>`.
    *   **Cara Kerja:** Bot akan mengambil log error relevan dari `journalctl`, mengidentifikasi pesan kunci, dan (menggunakan bantuan model AI sederhana) memberikan ringkasan masalah dan saran perbaikan yang mungkin.
*   **Laporan Mingguan:** Setiap hari Senin, bot akan mengirimkan ringkasan kinerja server selama seminggu terakhir: rata-rata penggunaan CPU/RAM, total data yang diunduh/diunggah, dan ringkasan backup.
*   **Manajemen *Dotfiles* & Konfigurasi:** Menu untuk mengelola file konfigurasi penting (misalnya, `.bashrc`, `.profile`, konfigurasi Nginx) dengan kemampuan untuk melihat, mengedit, dan memulihkan dari *backup* Git.
