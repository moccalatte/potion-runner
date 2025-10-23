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
    await update.message.reply_text("Pilih perintah Docker:", reply_markup=DOCKER_MENU)


async def list_containers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists running Docker containers."""
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    log_action("docker.ps", user_id=user_id, result="start")
    result = await run_cmd("docker ps", check=False, shell=True)

    if result.returncode == 0:
        output = result.stdout or "(no output)"
        message = f"<pre>{output}</pre>"
        await update.message.reply_text(wrap_success(message))
        log_action("docker.ps", user_id=user_id, result="ok")
    else:
        output = result.stderr or "(no error message)"
        message = f"<pre>{output}</pre>"
        await update.message.reply_text(wrap_failure(message))
        log_action("docker.ps", user_id=user_id, result="fail", detail=output)


async def stop_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to stop a container."""
    await update.message.reply_text("Please enter the container name or ID to stop.")
    return CONTAINER_NAME_STOP


async def stop_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stops a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    log_action("docker.stop", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "stop", container], check=False)

    if result.returncode == 0:
        await update.message.reply_text(wrap_success(f"Container {container} stopped."), reply_markup=DOCKER_MENU)
        log_action("docker.stop", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(result.stderr or "Unknown error"), reply_markup=DOCKER_MENU)
        log_action("docker.stop", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def restart_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to restart a container."""
    await update.message.reply_text("Please enter the container name or ID to restart.")
    return CONTAINER_NAME_RESTART


async def restart_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restarts a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    log_action("docker.restart", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "restart", container], check=False)

    if result.returncode == 0:
        await update.message.reply_text(wrap_success(f"Container {container} restarted."), reply_markup=DOCKER_MENU)
        log_action("docker.restart", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(result.stderr or "Unknown error"), reply_markup=DOCKER_MENU)
        log_action("docker.restart", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def logs_container_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to get container logs."""
    await update.message.reply_text("Please enter the container name or ID to get logs from.")
    return CONTAINER_NAME_LOGS


async def logs_container(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets logs from a Docker container."""
    container = update.message.text
    user_id = update.effective_user.id
    log_action("docker.logs", user_id=user_id, result="start", detail=container)
    result = await run_cmd(["docker", "logs", container], check=False)

    if result.returncode == 0:
        output = result.stdout or "(no output)"
        message = f"Logs for {container}:\n<pre>{output}</pre>"
        await update.message.reply_text(wrap_success(message), reply_markup=DOCKER_MENU)
        log_action("docker.logs", user_id=user_id, result="ok", detail=container)
    else:
        await update.message.reply_text(wrap_failure(result.stderr or "Unknown error"), reply_markup=DOCKER_MENU)
        log_action("docker.logs", user_id=user_id, result="fail", detail=result.stderr)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the conversation."""
    await update.message.reply_text("Operation cancelled.", reply_markup=DOCKER_MENU)
    return ConversationHandler.END
