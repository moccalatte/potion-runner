# Preview

## Ringkasan Cepat
- Bot async `python-telegram-bot` v21 kini memanfaatkan lock proses tunggal, logging aksi/runtime, serta menu Telegram lengkap dengan kontrol whitelist & threshold baru. ✅
- Sistem rsync + manifest SHA256 didukung deduplikasi jadwal (skip bila snapshot terbaru) serta cakupan cadangan yang mencakup `.env` dan sumber tambahan yang bisa dikonfigurasi. ✅

## Kekurangan / Risiko Tersisa
- Skrip `scripts/update_timer.py` tetap butuh akses sudo non-password; tanpa rule baru jadwal timer tidak ikut tersinkron saat `/set_backup`. ✅
- Berkas `.env` kini dicadangkan; pastikan media backup dan manifest disimpan di lokasi dengan akses ketat agar kredensial tidak bocor. ✅
- Akurasi `TIMEZONE` di `.env` krusial: salah zona waktu bisa membuat toleransi 45 menit melewati jadwal backup seharusnya. ✅
- Command `/apt_update` masih bergantung pada konfigurasi sudoers non-interaktif; tanpa itu bot akan menolak menjalankan pembaruan apt. ✅

## Anomali / Ambiguitas
- Pastikan sudoers juga mengizinkan menjalankan `scripts/update_timer.py` agar balasan sukses dari bot benar-benar berarti timer telah diperbarui. ✅
- `BACKUP_INCLUDE` menerima path relatif maupun absolut; perlu SOP internal supaya tidak ada folder besar atau rahasia lain yang ikut dicadangkan tanpa sengaja. ✅

## Rencana Selanjutnya
- Siapkan contoh rule sudoers tambahan untuk `scripts/update_timer.py` dan command admin baru supaya onboarding tim cepat. ✅
- Tambahkan test otomatis untuk handler `/set_threshold`, `/svc_add`, dan `/svc_remove` agar regresi mudah terdeteksi. ✅
- Evaluasi opsi enkripsi atau offsite storage untuk snapshot yang mengandung `.env`. ✅

## Instruksi Laptop Jadul (Segera Dijadwalkan)
- Tambahkan rule sudoers tanpa password untuk `sudo /opt/potion-runner/scripts/update_timer.py --time <HH:MM>` serta perintah `apt update/upgrade` agar bot bisa menyinkronkan jadwal dan update paket. ☑️
- Jalankan `sudo /opt/potion-runner/scripts/update_timer.py --time 02:30` sekali setelah deploy supaya timer systemd memakai jadwal baru. ☑️
- Pastikan paket `speedtest-cli` terpasang (`sudo apt install speedtest-cli`) agar menu speed test bekerja penuh. ☑️
- Review ulang `.env` (khususnya `TIMEZONE`, `BACKUP_INCLUDE`, dan whitelist service) lalu simpan perubahan melalui `/set_threshold` atau `/svc_add` sesuai kebutuhan. ☑️
- Reload daemon dan restart unit terkait: `sudo systemctl daemon-reload && sudo systemctl restart potion-runner.service potion-runner-backup.timer potion-runner-health.timer`. ☑️
