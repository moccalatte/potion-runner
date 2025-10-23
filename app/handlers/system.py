"""System command handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import wrap_failure, wrap_success
from ..utils.logging import log_action
from ..utils.shell import run_cmd


async def run_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs a shell command."""
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /run <command>")
        return

    command = " ".join(context.args)
    log_action("system.run", user_id=user_id, result="start", detail=command)
    result = await run_cmd(command, check=False, shell=True)

    if result.returncode == 0:
        output = result.stdout or "(no output)"
        message = f"<code>$ {command}</code>\n\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_success(message))
        log_action("system.run", user_id=user_id, result="ok", detail=command)
    else:
        output = result.stderr or "(no error message)"
        message = f"<code>$ {command}</code>\n\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_failure(message))
        log_action("system.run", user_id=user_id, result="fail", detail=command)
