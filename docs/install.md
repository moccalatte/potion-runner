# Instalasi Potion Runner Bot (Ubuntu 24.04 LTS)

Panduan ini mengikuti PRD potion runner dan ditulis untuk pengguna pemula Linux. Seluruh perintah dijalankan pada laptop ASUS X450L via SSH (user `dre`).

## 1. Update Sistem
```bash
sudo apt update && sudo apt upgrade -y
```
Menjamin paket terbaru dan keamanan.

## 2. Pasang Paket Wajib
```bash
sudo apt install -y python3-venv python3-pip git rsync lm-sensors acl
# Opsional: smartctl & tailscale
sudo apt install -y smartmontools tailscale
```
- `venv/pip` untuk lingkungan Python.
- `rsync` untuk backup incremental.
- `lm-sensors` membaca suhu (jalankan `sudo sensors-detect`).
- `acl` membantu pengelolaan izin file.

## 3. Siapkan HDD 500 GB (`/mnt/potion-data`)
1. Cek partisi:
   ```bash
   lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID
   ```
2. Jika partisi target (`/dev/sdb4` atau `/dev/sdb5`) belum ext4:
   ```bash
   sudo mkfs.ext4 -L POTIONDATA /dev/sdb4
   ```
3. Dapatkan UUID:
   ```bash
   sudo blkid /dev/sdb4
   ```
4. Tambahkan ke `/etc/fstab`:
   ```
   UUID=<UUIDSDB4> /mnt/potion-data ext4 defaults,noatime 0 2
   ```
5. Mount ulang dan verifikasi:
   ```bash
   sudo mkdir -p /mnt/potion-data
   sudo mount -a
   df -h
   ```

## 4. Salin Kode ke `/opt/potion-runner`
```bash
sudo mkdir -p /opt/potion-runner
sudo chown -R dre:dre /opt/potion-runner
rsync -a --delete ./ /opt/potion-runner/
```
(Rsync di atas diasumsikan dijalankan dari repo lokal ini.)

## 5. Opsional: Symlink Logs & Backup ke HDD
```bash
mkdir -p /mnt/potion-data/potion-runner-{logs,backups}
ln -s /mnt/potion-data/potion-runner-logs /opt/potion-runner/logs
ln -s /mnt/potion-data/potion-runner-backups /opt/potion-runner/backups
```

## 6. Buat Virtualenv & Install Dependensi
```bash
python3 -m venv /opt/potion-runner/venv
/opt/potion-runner/venv/bin/pip install --upgrade pip
/opt/potion-runner/venv/bin/pip install -r /opt/potion-runner/requirements.lock
```
Perintah di atas memasang `python-telegram-bot` dengan ekstra `job-queue`, sehingga APScheduler tersedia dan fitur JobQueue PTB aktif. Jadwal backup pada `.env` gunakan format `HH:MM` (mis. `02:30`); tanda titik otomatis diubah menjadi titik dua.

## 7. Konfigurasi `.env`
```bash
install -m 600 /dev/null /opt/potion-runner/.env
nano /opt/potion-runner/.env
```
Isi berdasarkan `.env.example` (token bot, admin ID, path, whitelist service).

## 8. Logrotate
Salin file template:
```bash
sudo cp /opt/potion-runner/ops/logrotate/potion-runner /etc/logrotate.d/potion-runner
sudo logrotate -f /etc/logrotate.d/potion-runner
```

## 9. Systemd Service & Timer
```bash
sudo cp /opt/potion-runner/ops/systemd/potion-runner.service /etc/systemd/system/
sudo cp /opt/potion-runner/ops/systemd/potion-runner-backup.service /etc/systemd/system/
sudo cp /opt/potion-runner/ops/systemd/potion-runner-backup.timer /etc/systemd/system/
sudo cp /opt/potion-runner/ops/systemd/potion-runner-health.service /etc/systemd/system/
sudo cp /opt/potion-runner/ops/systemd/potion-runner-health.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now potion-runner.service
sudo systemctl enable --now potion-runner-backup.timer
sudo systemctl enable --now potion-runner-health.timer
```
Verifikasi:
```bash
systemctl status potion-runner
journalctl -u potion-runner -f
```

## 10. Sensors (Opsional)
```bash
sudo sensors-detect
sensors
```

## 11. Uji Coba Bot
1. Kirim `/start` dan tekan tombol `📊 Status` → ringkasan sistem tampil.
2. `📜 Logs → /log_runtime` → tail runtime.
3. `💾 Backup → /backup_now` → snapshot muncul di HDD.
4. Cabut layanan dummy dari whitelist lalu cek alert service.

## 12. Operasional Harian
- Restart bot: `sudo systemctl restart potion-runner`.
- Lihat log: `journalctl -u potion-runner -f` atau `tail -f /opt/potion-runner/logs/runtime.log`.
- Trigger backup manual: tombol `💾 Backup now` atau `/backup_now`.

Selamat! Potion Runner Bot siap menjaga server jadul kamu. 🧃
