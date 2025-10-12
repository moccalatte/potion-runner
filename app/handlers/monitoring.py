"""Monitoring related handlers."""
from __future__ import annotations

from html import escape

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_success
from ..services.metrics import collect_metrics, metrics_summary
from ..utils.format import human_duration, render_table
from ..utils.logging import log_action


async def show_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    pending = await update.message.reply_text(PROCESSING)
    metrics = collect_metrics(settings)

    rows = [
        ("CPU", f"{metrics.cpu_percent:.1f}%"),
        ("Load", ", ".join(f"{val:.2f}" for val in metrics.load_avg)),
        ("RAM", f"{metrics.mem_percent:.1f}%"),
        ("RAM tersisa", f"{metrics.mem_available_mb():.0f} MB"),
        ("Disk /", f"{metrics.disk_root_percent:.1f}%"),
        ("Uptime", human_duration(metrics.uptime_seconds)),
    ]
    if metrics.disk_hdd_percent is not None:
        rows.append(("Disk HDD", f"{metrics.disk_hdd_percent:.1f}%"))
    if metrics.temperatures:
        top = max(metrics.temperatures, key=lambda temp: temp.current)
        rows.append(("Suhu", f"{top.label} {top.current:.0f}°C"))

    summary = metrics_summary(metrics)
    detail = render_table([(name, value) for name, value in rows])
    detail_block = f"<pre>{escape(detail)}</pre>" if detail else ""

    final_text = f"{wrap_success(summary)}\n\n{detail_block}".strip()
    await update.message.reply_text(final_text, reply_markup=MAIN_MENU)

    try:
        await pending.delete()
    except TelegramError:
        pass

    log_action("monitoring.status", user_id=update.effective_user.id, result="ok", detail=summary)


async def uptime_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    metrics = collect_metrics(settings)
    uptime = human_duration(metrics.uptime_seconds)
    if metrics.temperatures:
        temps_lines = "\n".join(
            f"• {escape(item.label)}: {item.current:.0f}°C" for item in metrics.temperatures
        )
        temps_section = f"Detail suhu:\n{temps_lines}"
    else:
        temps_section = "Sensor suhu belum kebaca."

    text = f"{wrap_success(f'Uptime {uptime}')}\n\n{temps_section}"
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("monitoring.uptime", user_id=update.effective_user.id, result="ok", detail=text)


__all__ = ["show_status", "uptime_detail"]
