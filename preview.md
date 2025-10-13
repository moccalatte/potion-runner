# Preview

## Ringkasan Cepat
- Backup malam hari tidak lagi gagal karena `Settings` kini diteruskan ke penulis manifest (`app/services/backup_svc.py`).
- Menjalankan `python3 -m compileall app scripts` memastikan tidak ada error sintaks/NameError tersisa di modul utama.

## Kekurangan / Risiko Tersisa
- Belum tersedia test otomatis untuk alur backup sehingga regresi serupa sulit terdeteksi dini.
- Hak sudo non-password untuk `scripts/update_timer.py` masih wajib agar sinkronisasi timer berjalan, namun belum ada verifikasi otomatis.

## Anomali / Ambiguitas
- Scheduler backup bergantung pada zona waktu `.env`; konfigurasi salah akan membuat toleransi 45 menit melewati jadwal seharusnya.
- Direktori tambahan pada `BACKUP_INCLUDE` bisa memasukkan data sensitif bila tidak diaudit rutin.

## Rencana Selanjutnya
- Tambahkan unit test minimal untuk `perform_backup`/`_write_manifest` guna menangkap error konfigurasi di pipeline CI.
- Dokumentasikan SOP pengecekan akses sudo untuk `update_timer.py` saat onboarding server baru.
