"""Network information handlers."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..services.net import IPInterface, ip_info, ping, speed_quick, tailscale_status
from ..utils.logging import log_action


async def network_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    interfaces = await ip_info()
    summary = ["Interface aktif:"]
    summary.extend(_format_interface_rows(interfaces))
    summary.append("Perintah: /ping, /speed, /tailscale")
    await update.message.reply_text("\n".join(summary), reply_markup=MAIN_MENU)
    log_action("network.menu", user_id=update.effective_user.id, result="ok", detail="menu")


def _format_interface_rows(interfaces: list[IPInterface]) -> list[str]:
    rows: list[str] = []
    for iface in interfaces:
        rows.append(f"• {iface.name}: {', '.join(iface.addresses)}")
    if not rows:
        rows.append("Tidak ada alamat aktif.")
    return rows


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    host = context.args[0] if context.args else settings.ping_host
    pending = await update.message.reply_text(PROCESSING)
    result = await ping(host)
    text = result.stdout or result.stderr or "Ping tidak memberikan output."
    await pending.edit_text(wrap_success(text))
    log_action("network.ping", user_id=update.effective_user.id, result="ok", detail=host)


async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = await update.message.reply_text(PROCESSING)
    text = await speed_quick()
    await pending.edit_text(text)
    log_action("network.speed", user_id=update.effective_user.id, result="ok", detail=text)


async def tailscale_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = await update.message.reply_text(PROCESSING)
    text = await tailscale_status()
    await pending.edit_text(text[:3500])
    log_action("network.tailscale", user_id=update.effective_user.id, result="ok", detail=text[:200])


__all__ = ["network_menu", "ping_command", "speed_command", "tailscale_command"]
