### 🔁 soal fitur “pemeliharaan otomatis”

bagian ini bagus buat ditambah di **menu 🪛 Maintenance**, ringan tapi membantu.
beberapa ide praktis:

| kategori              | contoh fitur                                  | keterangan                                                |
| --------------------- | --------------------------------------------- | --------------------------------------------------------- |
| **System Health**     | auto clean cache, rotate logs                 | `sudo apt autoremove`, `sudo journalctl --vacuum-time=7d` |
| **Disk Monitor**      | hapus file tmp besar, sisa space              | scan `/tmp`, `/var/log`                                   |
| **Restart Scheduler** | reboot tiap minggu dini hari                  | biar server segar & bersih cache                          |
| **Temp Cleanup**      | hapus `.pyc`, cache pip, snap lama            | `sudo apt autoremove --purge`                             |
| **Health Report**     | kirim ringkasan status via Telegram tiap pagi | CPU, RAM, HDD, suhu                                       |

> Catatan: pengecekan integritas backup sudah tersedia di bot melalui `/backup_verify`, jadi tidak perlu dimasukkan lagi di rencana fitur.

semua itu bisa kamu taruh di satu handler baru: `maintenance.py`,
dan tiap fitur dikaitkan ke tombol menu + emoji kayak:
`[ 🧹 Bersihin Cache ] [ 🩺 Cek Kesehatan ] [ 🔁 Update Sistem ]`.

---

## Tambahan

- Jadwalkan pengecekan status layanan penting (`systemctl status <service>`) biar cepat sadar kalau ada servis mati.
- Pantau konsumsi resource real-time (misal lewat `htop`/`glances`) dan catat lonjakan besar untuk evaluasi.
- Arsipkan ringkasan log error harian supaya tindakan koreksi bisa lebih terarah.
- Verifikasi koneksi keluar masuk (ping service utama atau cek health endpoint) untuk memastikan jalur trafik tetap sehat.
