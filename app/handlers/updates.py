"""Update and maintenance handlers."""
from __future__ import annotations

from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..utils.logging import log_action
from ..utils.shell import run_cmd


async def update_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Menu maintenance harian:\n"
        "• /apt_update → jalanin apt update + upgrade aman\n"
        "• /pip_sync → sinkron pip sesuai requirements.lock\n"
        "• /git_pull → tarik perubahan repo"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("updates.menu", user_id=update.effective_user.id, result="ok", detail="menu")


async def apt_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Akses ini khusus admin ya, minta izin dulu kalau perlu.")
        return
    pending = await update.message.reply_text(PROCESSING)
    sudo_check = await run_cmd(("sudo", "-n", "true"), check=False)
    if sudo_check.returncode != 0:
        hint = (
            "Belum ada izin sudo tanpa password untuk apt update. Tambahkan rule sudoers dulu ya."
        )
        await pending.edit_text(wrap_failure(hint))
        log_action("updates.apt", user_id=user_id, result="deny", detail=sudo_check.stderr)
        return
    result = await run_cmd(
        (
            "bash",
            "-lc",
            "sudo apt update && sudo apt upgrade -y",
        ),
        check=False,
    )
    if result.returncode == 0:
        await pending.edit_text(wrap_success("APT update sukses."))
        log_action("updates.apt", user_id=user_id, result="ok", detail=result.stdout)
    else:
        await pending.edit_text(wrap_failure(result.stderr or result.stdout))
        log_action("updates.apt", user_id=user_id, result="fail", detail=result.stderr)


async def pip_sync(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Akses ini khusus admin ya, minta izin dulu kalau perlu.")
        return
    pending = await update.message.reply_text(PROCESSING)
    requirements = settings.data_dir / "requirements.lock"
    if not requirements.exists():
        await pending.edit_text(wrap_failure("requirements.lock belum tersedia. Generate dulu ya."))
        return
    pip_path = settings.data_dir / "venv" / "bin" / "pip"
    if not pip_path.exists():
        await pending.edit_text(
            wrap_failure("Venv belum ada. Jalankan setup venv dulu baru lanjut.")
        )
        return
    command = (str(pip_path), "install", "-r", str(requirements))
    result = await run_cmd(command, check=False)
    if result.returncode == 0:
        await pending.edit_text(wrap_success("Pip sinkron sukses."))
        log_action("updates.pip", user_id=user_id, result="ok", detail=result.stdout)
    else:
        await pending.edit_text(wrap_failure(result.stderr or result.stdout))
        log_action("updates.pip", user_id=user_id, result="fail", detail=result.stderr)


async def git_pull(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Akses ini khusus admin ya, minta izin dulu kalau perlu.")
        return
    pending = await update.message.reply_text(PROCESSING)
    result = await run_cmd(
        (
            "git",
            "-C",
            str(settings.data_dir / "app"),
            "pull",
        ),
        check=False,
    )
    if result.returncode == 0:
        await pending.edit_text(wrap_success(result.stdout or "Git up to date."))
        log_action("updates.git", user_id=user_id, result="ok", detail=result.stdout)
    else:
        await pending.edit_text(wrap_failure(result.stderr or result.stdout))
        log_action("updates.git", user_id=user_id, result="fail", detail=result.stderr)


__all__ = ["update_menu", "apt_update", "pip_sync", "git_pull"]
