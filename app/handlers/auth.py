"""User authorization handlers."""
from __future__ import annotations

import random

from telegram import Update
from telegram.ext import ApplicationHandlerStop, ContextTypes

from ..config import Settings

_REJECTIONS = [
    (
        "Wahai non-admin yang budiman,\n"
        "Maaf, aksesmu cuma sebatas angan-angan.\n"
        "Fitur ini dijaga ketat, bukan buat mainan, 🤖\n"
        "Cuma para admin yang punya kunci ke gerbang kayangan."
    ),
    (
        "Pintu ini terkunci, kawan,\n"
        "Kecuali namamu ada di daftar para dewan.\n"
        "Coba lagi nanti kalau sudah dapat wangsit, 🤣\n"
        "Atau kalau admin sudah memberimu sedikit jimat sakti."
    ),
    (
        "Hehehe, mau ke mana, tuan?\n"
        "Jalan ini khusus untuk para kaisar, bukan sembarang bangsawan.\n"
        "Balik kanan grak! Sebelum kena semprot firewall kerajaan. 🔥"
    ),
]


async def guard_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blocks non-admin users from accessing handlers other than /start."""
    # Allow /start for everyone
    if update.message and update.message.text and update.message.text.startswith("/start"):
        return

    settings: Settings = context.bot_data["settings"]
    user = update.effective_user

    # Allow admins to proceed
    if user and settings.is_admin(user.id):
        return

    # For non-admins, send rejection and stop further handlers
    rejection = random.choice(_REJECTIONS)
    if update.message:
        await update.message.reply_text(rejection)

    # Stop handling other commands in the same group and other groups.
    raise ApplicationHandlerStop
