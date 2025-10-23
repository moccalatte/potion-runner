"""Network information handlers."""
from __future__ import annotations

from html import escape

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..services.net import IPInterface, ip_info, ping, speed_quick, tailscale_status
from ..utils.logging import log_action
from ..utils.shell import run_cmd


async def network_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    interfaces = await ip_info()
    summary = ["Interface aktif di server kamu:"]
    summary.extend(_format_interface_rows(interfaces))
    summary.append("Perintah cepat: /ping, /speed, /tailscale")
    await update.message.reply_text("\n".join(summary), reply_markup=MAIN_MENU)
    log_action("network.menu", user_id=update.effective_user.id, result="ok", detail="menu")


def _format_interface_rows(interfaces: list[IPInterface]) -> list[str]:
    rows: list[str] = []
    for iface in interfaces:
        safe_addresses = ", ".join(escape(addr) for addr in iface.addresses)
        rows.append(f"• {escape(iface.name)}: {safe_addresses}")
    if not rows:
        rows.append("Tidak ada alamat aktif.")
    return rows


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    host = context.args[0] if context.args else settings.ping_host
    pending = await update.message.reply_text(PROCESSING)
    result = await ping(host)
    text = result.stdout or result.stderr or "Ping tidak memberikan output."
    payload = f"Hasil ping ke {escape(host)}:\n{text}" if text else f"Hasil ping ke {escape(host)} tidak ada respons."
    await pending.edit_text(wrap_success(payload[:3500]))
    log_action("network.ping", user_id=update.effective_user.id, result="ok", detail=host)


async def speed_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs a speed test with real-time feedback."""
    user_id = update.effective_user.id

    pending = await update.message.reply_text("Oke, mulai tes kecepatan... 💨")
    log_action("network.speed", user_id=user_id, result="start")

    try:
        await pending.edit_text("Menguji kecepatan unduh... 📥")
        # We run the simple test first to get a baseline
        result = await run_cmd(["speedtest-cli", "--simple"], check=True, timeout=120)

        await pending.edit_text("Menguji kecepatan unggah... 📤")
        # Run again to get the final result, this is a limitation of speedtest-cli's output
        result = await run_cmd(["speedtest-cli", "--simple"], check=True, timeout=120)

        output = result.stdout
        lines = [line.strip() for line in output.split('\n')]

        def parse_line(key):
            try:
                line = next(l for l in lines if key in l)
                return line.split(': ')[1]
            except (StopIteration, IndexError):
                return "N/A"

        ping = parse_line("Ping")
        download = parse_line("Download")
        upload = parse_line("Upload")

        final_message = (
            f"Taraa! 🚀 Ini dia hasilnya:\n\n"
            f"<b>Ping:</b> {ping}\n"
            f"<b>Download:</b> {download}\n"
            f"<b>Upload:</b> {upload}"
        )

        await pending.edit_text(wrap_success(final_message))
        log_action("network.speed", user_id=user_id, result="ok", detail=output)

    except Exception as e:
        error_message = f"Waduh, sepertinya ada masalah dengan `speedtest-cli`... 🤔\n\nError: {str(e)}"
        await pending.edit_text(wrap_failure(error_message))
        log_action("network.speed", user_id=user_id, result="fail", detail=str(e))


async def tailscale_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pending = await update.message.reply_text(PROCESSING)
    text = await tailscale_status()
    await pending.edit_text(wrap_success(f"Status Tailscale:\n{text}"[:3500]))
    log_action("network.tailscale", user_id=update.effective_user.id, result="ok", detail=text[:200])


__all__ = ["network_menu", "ping_command", "speed_command", "tailscale_command"]
