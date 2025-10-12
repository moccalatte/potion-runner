"""Administrative helpers."""
from __future__ import annotations

import datetime as dt
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, wrap_failure, wrap_success
from ..services.metrics import HealthMonitor
from ..utils.envfile import update_env_file
from ..utils.logging import log_action
from ..utils.shell import run_cmd


async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    backup_schedule = context.bot_data.get("backup_schedule", settings.backup_schedule)
    text = (
        "Pengaturan cepat:\n"
        f"• Jadwal backup sekarang: {backup_schedule}\n"
        "• /set_backup &lt;HH:MM&gt; → ubah jadwal backup\n"
        "• /admins → lihat admin terdaftar\n"
        "• /alerts → status alert"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("admin.menu", user_id=update.effective_user.id, result="ok", detail="menu")


async def admins_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    admins = "\n".join(str(admin) for admin in sorted(settings.admin_ids))
    await update.message.reply_text(f"Admin terdaftar:\n{admins}")
    log_action("admin.list", user_id=update.effective_user.id, result="ok", detail=admins)


async def set_backup_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur ini khusus admin ya, hubungi PIC kalau butuh akses.")
        return
    if not context.args:
        await update.message.reply_text("Formatnya: /set_backup HH:MM")
        return
    raw_value = context.args[0].replace(".", ":")
    try:
        parsed = dt.datetime.strptime(raw_value, "%H:%M")
    except ValueError:
        await update.message.reply_text("Format salah. Pakai format HH:MM (24 jam).")
        return
    value = parsed.strftime("%H:%M")
    context.bot_data["backup_schedule"] = value
    reschedule = context.bot_data.get("reschedule_backup_job")
    if callable(reschedule):
        reschedule(value)
    settings.backup_schedule = value
    update_env_file(settings.env_file, {"BACKUP_SCHEDULE": value})
    sync_result = await _sync_backup_timer(settings, value)
    await update.message.reply_text(wrap_success(f"Backup dijadwalkan ulang ke {value}"))
    log_action("admin.set_backup", user_id=user_id, result="ok", detail=value)
    if sync_result:
        await update.message.reply_text(sync_result)


async def alerts_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    disabled = context.bot_data.setdefault("alerts_disabled", {})
    if not disabled:
        await update.message.reply_text(
            "Semua alert aktif. Gunakan /alert_disable &lt;kode&gt; &lt;menit&gt; untuk snooze."
        )
        return
    lines = ["Alert dimatikan sementara:"]
    now = dt.datetime.now(dt.timezone.utc)
    for code, expiry in list(disabled.items()):
        expire_at = dt.datetime.fromisoformat(expiry)
        if expire_at < now:
            disabled.pop(code, None)
            continue
        remaining = int((expire_at - now).total_seconds() // 60)
        lines.append(f"• {escape(code)} (sisa {remaining} menit)")
    await update.message.reply_text("\n".join(lines))


async def alert_disable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur ini khusus admin ya, hubungi PIC kalau butuh akses.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Gunakan /alert_disable &lt;kode&gt; &lt;menit&gt;.")
        return
    code = context.args[0]
    try:
        minutes = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Menit harus angka.")
        return
    expiry = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=minutes)
    disabled = context.bot_data.setdefault("alerts_disabled", {})
    disabled[code] = expiry.isoformat()
    await update.message.reply_text(
        wrap_success(f"Alert {code} off hingga {expiry:%H:%M UTC}")
    )
    log_action("admin.alert_disable", user_id=user_id, result="ok", detail=f"{code} {minutes}")


async def set_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Pengaturan threshold cuma buat admin ya.")
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Format: /set_threshold <cpu|ram|disk|temp|hysteresis> <nilai>."
        )
        return
    metric = context.args[0].lower()
    raw_value = context.args[1]
    mapping = {
        "cpu": ("THRESHOLD_CPU", "cpu_percent", float),
        "ram": ("THRESHOLD_RAM_MB", "ram_free_mb", float),
        "disk": ("THRESHOLD_DISK", "disk_percent", float),
        "temp": ("THRESHOLD_TEMP", "temperature_c", float),
        "hysteresis": ("THRESHOLD_HYSTERESIS_MIN", "hysteresis_minutes", int),
    }
    if metric not in mapping:
        await update.message.reply_text("Metric tidak dikenali. Pilih: cpu, ram, disk, temp, hysteresis.")
        return
    env_key, attr, caster = mapping[metric]
    try:
        value = caster(raw_value)
    except ValueError:
        await update.message.reply_text("Nilai tidak valid.")
        return
    setattr(settings.thresholds, attr, value)
    update_env_file(settings.env_file, {env_key: str(value)})
    context.bot_data["health_monitor"] = HealthMonitor(settings.thresholds)
    await update.message.reply_text(wrap_success(f"Threshold {metric} diperbarui."))
    log_action("admin.threshold", user_id=user_id, result="ok", detail=f"{metric}={value}")


async def service_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur whitelist cuma untuk admin.")
        return
    if not context.args:
        await update.message.reply_text("Format: /svc_add <nama.service>")
        return
    service = context.args[0]
    if not service.endswith(".service"):
        service = f"{service}.service"
    check = await run_cmd(("systemctl", "status", service), check=False)
    if check.returncode != 0:
        await update.message.reply_text(wrap_failure(check.stderr or "Service tidak ditemukan."))
        log_action("admin.svc_add", user_id=user_id, result="fail", detail=service)
        return
    if service in settings.services_whitelist:
        await update.message.reply_text(wrap_success("Service sudah ada di whitelist."))
        return
    settings.services_whitelist.append(service)
    _persist_services(settings)
    await update.message.reply_text(wrap_success(f"{service} ditambahkan ke whitelist."))
    log_action("admin.svc_add", user_id=user_id, result="ok", detail=service)


async def service_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur whitelist cuma untuk admin.")
        return
    if not context.args:
        await update.message.reply_text("Format: /svc_remove <nama.service>")
        return
    service = context.args[0]
    if not service.endswith(".service"):
        service = f"{service}.service"
    if service not in settings.services_whitelist:
        await update.message.reply_text("Service belum ada di whitelist.")
        return
    settings.services_whitelist.remove(service)
    _persist_services(settings)
    await update.message.reply_text(wrap_success(f"{service} dihapus dari whitelist."))
    log_action("admin.svc_remove", user_id=user_id, result="ok", detail=service)


def _persist_services(settings: Settings) -> None:
    joined = ",".join(settings.services_whitelist)
    update_env_file(settings.env_file, {"SERVICES_WHITELIST": joined})


async def _sync_backup_timer(settings: Settings, value: str) -> str | None:
    script = settings.data_dir / "scripts" / "update_timer.py"
    if not script.exists():
        return None
    result = await run_cmd(("sudo", "-n", str(script), "--time", value), check=False)
    if result.returncode != 0:
        return wrap_failure(
            result.stderr
            or "Timer systemd belum ikut berubah. Jalankan skrip update_timer.py dengan sudo."
        )
    return wrap_success("Timer systemd ikut disinkronkan.")


__all__ = [
    "settings_menu",
    "admins_list",
    "set_backup_schedule",
    "alerts_status",
    "alert_disable",
    "set_threshold",
    "service_add",
    "service_remove",
]
