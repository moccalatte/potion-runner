"""Docker management handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from ..config import Settings
from ..menus import DOCKER_MENU, MAIN_MENU, wrap_failure, wrap_success
from ..utils.logging import log_action
from ..utils.shell import run_cmd

# Conversation states
CONTAINER_NAME_STOP, CONTAINER_NAME_RESTART, CONTAINER_NAME_LOGS = range(3)


async def docker_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the Docker menu."""
    await update.message.reply_text(
        "Ini dia menu buat ngatur para 'paus' di server kamu! 🐳\n"
        "Mau diapain nih, kapten?",
        reply_markup=DOCKER_MENU
    )


async def list_containers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists running Docker containers."""
    await update.message.reply_text("Oke, lagi aku intip dulu siapa aja yang lagi nongkrong di sini. Sabar ya... 🕵️‍♂️")
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Waduh, menu ini khusus buat admin. Kamu belum terdaftar, nih. 😅")
        return

    log_action("docker.ps", user_id=user_id, result="start")
    result = await run_cmd(["docker", "ps"], check=False)

    if result.returncode == 0:
        output = result.stdout.strip()
        if not output:
            message = "Sepi nih, nggak ada kontainer yang lagi jalan. 🤔"
        else:
            message = f"Ini dia daftar jagoan yang lagi aktif:\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_success(message))
        log_action("docker.ps", user_id=user_id, result="ok")
    else:
        output = result.stderr or "(no error message)"
        message = f"Gagal nih, nggak bisa lihat daftar kontainer. Mungkin Dockernya lagi ngambek. 😅\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_failure(message))
        log_action("docker.ps", user_id=user_id, result="fail", detail=output)


async def stop_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to stop a container."""
    await update.message.reply_text("Kontainer mana yang mau diberhentiin? Kasih tau nama atau ID-nya ya.")
    return CONTAINER_NAME_STOP


async def stop_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stops a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    await update.message.reply_text(f"Oke, aku coba hentiin `{container}`. Bentar ya...")
    log_action("docker.stop", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "stop", container], check=False)

    if result.returncode == 0:
        await update.message.reply_text(wrap_success(f"Kontainer `{container}` berhasil dihentikan. Tidur nyenyak ya, paus kecil. 😴"), reply_markup=DOCKER_MENU)
        log_action("docker.stop", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(f"Gagal menghentikan `{container}`. Dia bandel kayaknya. 😠\n<pre>{result.stderr or 'Unknown error'}</pre>"), reply_markup=DOCKER_MENU)
        log_action("docker.stop", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def restart_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to restart a container."""
    await update.message.reply_text("Siapa yang mau di-restart biar seger lagi? Kasih tau nama atau ID-nya.")
    return CONTAINER_NAME_RESTART


async def restart_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restarts a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    await update.message.reply_text(f"Siap! Aku restart dulu si `{container}`. Biar semangat lagi! 🔥")
    log_action("docker.restart", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "restart", container], check=False)

    if result.returncode == 0:
        await update.message.reply_text(wrap_success(f"Voila! Kontainer `{container}` udah fresh dan jalan lagi."), reply_markup=DOCKER_MENU)
        log_action("docker.restart", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(f"Yah, gagal restart `{container}`. Kayaknya dia lagi mager. 😩\n<pre>{result.stderr or 'Unknown error'}</pre>"), reply_markup=DOCKER_MENU)
        log_action("docker.restart", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def logs_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to get container logs."""
    await update.message.reply_text("Mau lihat catatan harian (log) dari kontainer mana nih?")
    return CONTAINER_NAME_LOGS


async def logs_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets logs from a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    await update.message.reply_text(f"Oke, aku cariin buku harian si `{container}`. Sebentar ya, lagi ngintip... 👀")
    log_action("docker.logs", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "logs", container], check=False)

    if result.returncode == 0:
        output = result.stdout or "(Kosong, nggak ada curhatan.)"
        message = f"Ini dia isi hatinya si `{container}`:\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_success(message), reply_markup=DOCKER_MENU)
        log_action("docker.logs", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(f"Waduh, nggak nemu buku hariannya. Kayaknya dia pemalu. 😥\n<pre>{result.stderr or 'Unknown error'}</pre>"), reply_markup=DOCKER_MENU)
        log_action("docker.logs", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Oke, batal. Kita balik lagi ke menu Docker ya.", reply_markup=DOCKER_MENU)
    return ConversationHandler.END
