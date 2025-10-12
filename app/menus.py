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

PROCESSING = (
    "Waduh, sepertinya sedang ramai… tapi tunggu sebentar ya 🧃. Lagi siapin datamu nih…"
)
DONE_OK = "Sudah siap nih! ✅ Info singkat: {summary}"
DONE_FAIL = "Hmm, ada kendala nih ❌. Rangkuman error: {error}. Coba lagi ya."
CONFIRM_TEMPLATE = "Yakin mau {action}? Balas YA untuk lanjut."


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
