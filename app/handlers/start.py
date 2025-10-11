"""Start/help handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU
from ..services.metrics import collect_metrics, metrics_summary
from ..utils.logging import log_action


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user = update.effective_user
    welcome = [
        f"Halo {user.mention_html()}!",
        "Selamat datang di Potion Runner Bot.",
        "Pilih menu di bawah untuk cek status server jadul kamu.",
    ]
    if not settings.is_admin(user.id):
        welcome.append("Mode baca saja. Hubungi admin untuk akses kontrol.")
    await update.message.reply_html("\n".join(welcome), reply_markup=MAIN_MENU)
    log_action("start", user_id=user.id, result="ok", detail="/start")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    text = (
        "Bot ini bantu kamu pantau & kontrol node.\n"
        "Menu utama pakai tombol Reply Keyboard.\n"
        "Gunakan /status untuk ringkasan cepat, /backup untuk backup instan,"
        " dan /services untuk daftar layanan whitelist."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("help", user_id=update.effective_user.id, result="ok", detail="/help")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    metrics = collect_metrics(settings)
    summary = metrics_summary(metrics)
    await update.message.reply_text(summary, reply_markup=MAIN_MENU)
    log_action("status", user_id=update.effective_user.id, result="ok", detail=summary)
