# Preview

## Poin Paling Penting
- Bot async `python-telegram-bot` v21 dengan job queue: monitoring, alert hysteresis, backup otomatis.
- Handler lengkap untuk menu 📊/🧰/📜/💾/🌐/🔄/⚙️ serta command lanjutan (logs, service, backup, network, update, admin).
- Wrapper `run_cmd` aman + logger runtime/actions, struktur folder sesuai PRD.
- Sistem backup menggunakan rsync + manifest sha256, script CLI mendukung systemd timer (jadwal otomatis dinormalisasi agar aman).
- Dokumentasi instalasi, template systemd & logrotate, `.env.example`, `requirements.lock` disertakan.

## Kekurangan / Risiko Tersisa
- Threshold alert dapat diubah hanya via `.env`; belum ada UI untuk konfigurasi granular per sensor.
- Speed test membutuhkan `speedtest-cli` atau `fast-cli`; jika tidak ada tool, bot hanya menampilkan instruksi.
- `apt_update` menjalankan `sudo` non-interaktif; diperlukan konfigurasi sudoers agar tidak diminta password.
- Backup rsync mengecualikan direktori/berkas di luar daftar default; tambahkan manual jika ada data lain yang perlu dicadangkan.
- Health timer & backup timer mengandalkan systemd + script CLI; pastikan path `/opt/potion-runner` konsisten dengan deploy asli.

## Ambiguitas / Hal Perlu Konfirmasi
- Daftar layanan whitelist di `.env` perlu disesuaikan secara manual; belum ada menu untuk menambah/menghapus.
- Penanganan suhu bergantung pada `psutil.sensors_temperatures`; perangkat tanpa sensor akan melewati informasi suhu.
- Tailscale status memerlukan paket `tailscale`; jika tidak dipasang hasil hanya pesan info.
- Installer script melakukan `rsync` dari repo lokal; pastikan dijalankan dari direktori sumber yang benar.
