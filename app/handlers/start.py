"""Start/help handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, wrap_success
from ..services.metrics import collect_metrics, metrics_summary
from ..utils.logging import log_action


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user = update.effective_user
    welcome = [
        f"Halo {user.mention_html()}! 👋",
        "Aku si Potion Runner Bot, partner jagain server kamu.",
        "Tinggal pencet menu di bawah buat ngecek resource atau jalanin aksi.",
    ]
    if not settings.is_admin(user.id):
        welcome.append("Saat ini mode baca aja ya. Minta akses admin kalau butuh kontrol penuh.")
    await update.message.reply_html("\n".join(welcome), reply_markup=MAIN_MENU)
    log_action("start", user_id=user.id, result="ok", detail="/start")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    text = (
        "Aku bantu pantau resource, cek log, sampai restart service.\n"
        "Semua fitur ada di tombol bawah layar.\n"
        "Shortcut: /status untuk snapshot cepat, /backup_now buat langsung backup, "
        "/svc_list lihat whitelist yang boleh dikontrol."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("help", user_id=update.effective_user.id, result="ok", detail="/help")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    metrics = collect_metrics(settings)
    summary = metrics_summary(metrics)
    await update.message.reply_text(wrap_success(summary), reply_markup=MAIN_MENU)
    log_action("status", user_id=update.effective_user.id, result="ok", detail=summary)
