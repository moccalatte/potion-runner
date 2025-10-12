"""Service control handlers."""
from __future__ import annotations

import asyncio
from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..services.sysctl import control_service, list_services
from ..utils.logging import log_action
from ..utils.shell import ShellCommandError


async def control_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    statuses = await list_services(settings)
    lines = ["Status layanan whitelist (yang aman buat diutak-atik):"]
    for status in statuses:
        indicator = "✅" if status.is_healthy() else "⚠️"
        safe_name = escape(status.name)
        safe_state = escape(status.active_state)
        safe_sub = escape(status.sub_state)
        lines.append(f"{indicator} {safe_name} → {safe_state}/{safe_sub}")
    lines.append("Butuh manual override? Pakai format: /svc &lt;start|stop|restart|status&gt; &lt;service&gt;.")
    await update.message.reply_text("\n".join(lines), reply_markup=MAIN_MENU)
    log_action("controls.menu", user_id=update.effective_user.id, result="ok", detail="menu")


async def service_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur ini cuma buat admin ya. Minta akses dulu kalau perlu.")
        log_action("controls.denied", user_id=user_id, result="deny", detail="not admin")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Formatnya: /svc &lt;aksi&gt; &lt;service&gt;. Contoh: /svc restart potion-runner.service"
        )
        return

    action = context.args[0].lower()
    service = context.args[1]

    pending = await update.message.reply_text(PROCESSING)
    if action == "status":
        statuses = await list_services(settings)
        match = next((s for s in statuses if s.name == service), None)
        if not match:
            await pending.edit_text(wrap_failure("Service yang dimaksud belum ada di whitelist."))
            log_action("controls.status", user_id=user_id, result="fail", detail=service)
            return
        msg = wrap_success(
            f"{service}: {match.active_state}/{match.sub_state} sejak {match.since}"
        )
        await pending.edit_text(msg)
        log_action("controls.status", user_id=user_id, result="ok", detail=service)
        return

    if action in {"restart", "stop"} and service == settings.self_service:
        await pending.edit_text(
            wrap_success(
                f"{action} {service} lagi dijalankan. Bot bakal offline sebentar trus balik lagi."
            )
        )
        context.application.create_task(
            _run_self_control(context, settings, service, action, update.effective_chat.id, user_id)
        )
        return

    await _run_control_with_feedback(
        context,
        settings,
        service,
        action,
        pending,
        user_id,
    )


async def _run_control_with_feedback(
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    service: str,
    action: str,
    pending_message,
    user_id: int,
) -> None:
    try:
        result = await control_service(settings, service, action)
    except ValueError as exc:
        await pending_message.edit_text(wrap_failure(str(exc)))
        log_action(f"controls.{action}", user_id=user_id, result="fail", detail=str(exc))
        return
    except ShellCommandError as exc:
        hint = (
            "Gagal jalanin systemctl karena butuh sudo tanpa password. "
            "Tambahkan rule sudoers agar command ini boleh jalan otomatis."
        )
        await pending_message.edit_text(wrap_failure(exc.stderr or hint))
        log_action(
            f"controls.{action}",
            user_id=user_id,
            result="fail",
            detail=f"{exc.stderr or exc.stdout}",
        )
        return

    if result.returncode == 0:
        message = wrap_success(f"{action} {service} sukses.")
        await pending_message.edit_text(message)
        log_action(
            f"controls.{action}",
            user_id=user_id,
            result="ok",
            detail=result.stdout,
        )
    else:
        message = wrap_failure(result.stderr or "systemctl gagal")
        await pending_message.edit_text(message)
        log_action(
            f"controls.{action}",
            user_id=user_id,
            result="fail",
            detail=result.stderr,
        )


async def _run_self_control(
    context: ContextTypes.DEFAULT_TYPE,
    settings: Settings,
    service: str,
    action: str,
    chat_id: int,
    user_id: int,
) -> None:
    await asyncio.sleep(1)
    try:
        await control_service(settings, service, action)
        log_action(
            f"controls.{action}",
            user_id=user_id,
            result="ok",
            detail="self-service restart",
        )
    except ShellCommandError as exc:
        hint = (
            "Gagal jalanin systemctl karena butuh sudo tanpa password. "
            "Tambahkan rule sudoers agar command ini boleh jalan otomatis."
        )
        await context.bot.send_message(chat_id=chat_id, text=wrap_failure(exc.stderr or hint))
        log_action(
            f"controls.{action}",
            user_id=user_id,
            result="fail",
            detail=f"{exc.stderr or exc.stdout}",
        )
    except ValueError as exc:
        await context.bot.send_message(chat_id=chat_id, text=wrap_failure(str(exc)))
        log_action(f"controls.{action}", user_id=user_id, result="fail", detail=str(exc))


__all__ = ["control_menu", "service_command"]
