"""Log related handlers."""
from __future__ import annotations

import asyncio
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..services.sysctl import tail_journal
from ..utils.logging import log_action


async def logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Pilih salah satu: /log_runtime, /log_journal &lt;service&gt;, /log_errors.\n"
        "Untuk kirim file penuh gunakan /log_file."
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("logs.menu", user_id=update.effective_user.id, result="ok", detail="menu")


async def log_runtime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    pending = await update.message.reply_text(PROCESSING)
    lines = await _tail_file(settings.runtime_log, 80)
    await pending.edit_text(wrap_success(f"Tail runtime.log:\n{lines}"))
    log_action("logs.runtime", user_id=update.effective_user.id, result="ok", detail="tail runtime")


async def log_errors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    pending = await update.message.reply_text(PROCESSING)
    lines = await _grep_file(settings.runtime_log, "error")
    if lines:
        await pending.edit_text(wrap_success("\n".join(lines[:30])))
    else:
        await pending.edit_text("Tidak ditemukan baris error.")
    log_action("logs.errors", user_id=update.effective_user.id, result="ok", detail="grep error")


async def log_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    path = settings.runtime_log
    if not path.exists():
        await update.message.reply_text("File runtime.log belum dibuat.")
        return
    await update.message.reply_document(document=path)
    log_action("logs.file", user_id=update.effective_user.id, result="ok", detail="runtime.log")


async def log_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not context.args:
        await update.message.reply_text("Gunakan /log_journal &lt;service&gt;.")
        return
    service = context.args[0]
    pending = await update.message.reply_text(PROCESSING)
    content = await tail_journal(service)
    await pending.edit_text(wrap_success(content))
    log_action("logs.journal", user_id=update.effective_user.id, result="ok", detail=service)


async def _tail_file(path: Path, lines: int) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _read_tail, path, lines)


def _read_tail(path: Path, lines: int) -> str:
    if not path.exists():
        return "File belum ada."
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        data = handle.readlines()[-lines:]
    return "".join(data)


async def _grep_file(path: Path, keyword: str) -> list[str]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _grep_sync, path, keyword)


def _grep_sync(path: Path, keyword: str) -> list[str]:
    if not path.exists():
        return []
    keyword = keyword.lower()
    matched = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if keyword in line.lower():
                matched.append(line.strip())
    return matched


__all__ = ["logs_menu", "log_runtime", "log_errors", "log_file", "log_journal"]
