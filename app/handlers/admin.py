"""Administrative helpers."""
from __future__ import annotations

import datetime as dt
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, wrap_failure, wrap_success
from ..utils.logging import log_action


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
        await update.message.reply_text("Khusus admin.")
        return
    if not context.args:
        await update.message.reply_text("Gunakan /set_backup HH:MM")
        return
    raw_value = context.args[0].replace(".", ":")
    try:
        parsed = dt.datetime.strptime(raw_value, "%H:%M")
    except ValueError:
        await update.message.reply_text("Format salah. Gunakan HH:MM (24 jam).")
        return
    value = parsed.strftime("%H:%M")
    context.bot_data["backup_schedule"] = value
    reschedule = context.bot_data.get("reschedule_backup_job")
    if callable(reschedule):
        reschedule(value)
    await update.message.reply_text(wrap_success(f"Backup dijadwalkan ulang ke {value}"))
    log_action("admin.set_backup", user_id=user_id, result="ok", detail=value)


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
        await update.message.reply_text("Khusus admin.")
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


__all__ = [
    "settings_menu",
    "admins_list",
    "set_backup_schedule",
    "alerts_status",
    "alert_disable",
]
