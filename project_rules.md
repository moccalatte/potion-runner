# PROJECT RULES
## ⚠️ Warning! Jangan pernah ubah isi file project_rules.md ini. 

## Lingkungan
- Cantumkan bahasa & versi terbaru atau paling stabil.
- Cara run harus jelas (contoh: `./run.sh` atau `python main.py`).
- Semua error harus ditangani dengan log yang jelas.
- Selalu buat gitignore beserta isinya terutama yang penting.
- Jika python, maka selalu gunakan venv.
- Selalu hasilkan .example seperti env.example ataupun file credentials .json.example dan lainnya.

## Logging & Error Handling
- Selalu aktifkan mode debug/log.
- Jangan biarkan loop jalan tanpa delay → harus ada sleep/backoff.
- Error fatal → log, exit dengan kode 1.

## Struktur Kode
- File tidak lebih dari 300–400 baris **setelah fitur stabil**.
- Setiap file/fungsi harus punya tanggung jawab tunggal (single responsibility).
- Hindari refactor besar tanpa permintaan eksplisit.

## Gaya Perubahan
- **Perubahan minimal:** patch kecil, bukan rewrite massal.
- Sertakan langkah verifikasi (cara cek fix berhasil).
- Sertakan rollback plan (cara balik ke sebelum patch).

## Protokol Debug
1. Ulangi error dengan jelas.
2. Catat environment (`php -v`, `python --version`, dll).
3. Lampirkan log/error singkat (10–20 baris).
4. Ajukan hipotesis → beri opsi solusi.
5. Terapkan patch kecil.
6. Verifikasi hasil.

## AI Interaction
- Jika tidak yakin, AI wajib jelaskan 2–3 hipotesis.
- Dilarang rename/pindah file kecuali diminta.
- Fokus jelaskan *kenapa error terjadi* sebelum kasih fix.
- Setelah selesai, selalu hasilkan `preview.md` yang merangkum poin kekurangan serta anomali dan ambigu yang ada projek.
