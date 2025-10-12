"""Telegram menu layouts and text templates."""
from __future__ import annotations

from html import escape

from telegram import ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📊 Status", "🧰 Kontrol"],
        ["📜 Logs", "💾 Backup"],
        ["🌐 Network", "🔄 Update"],
        ["⚙️ Settings"],
    ],
    resize_keyboard=True,
)

PROCESSING = "Oke, lagi aku cek dulu server kamu. Sabar sebentar ya ⚙️"
DONE_OK = "Beres! ✅ Ringkasan: {summary}"
DONE_FAIL = "Kenapa ya... ❌ Ada error: {error}. Coba ulang sebentar lagi, aku standby kok."
CONFIRM_TEMPLATE = "Yakin mau {action}? Balas YA kalau sudah mantap."


def wrap_success(summary: str) -> str:
    return DONE_OK.format(summary=escape(summary))


def wrap_failure(error: str) -> str:
    return DONE_FAIL.format(error=escape(error))


def confirm_text(action: str) -> str:
    return CONFIRM_TEMPLATE.format(action=escape(action))


__all__ = [
    "MAIN_MENU",
    "PROCESSING",
    "wrap_success",
    "wrap_failure",
    "CONFIRM_TEMPLATE",
    "confirm_text",
]
