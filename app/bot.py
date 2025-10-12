"""Potion Runner Bot entry point."""
from __future__ import annotations

import atexit
import datetime as dt
import fcntl
import os
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import Conflict
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    filters,
)

from .config import Settings, load_settings
from .handlers import (
    admin,
    backup,
    controls,
    logs,
    monitoring,
    network,
    start,
    updates,
)
from .menus import MAIN_MENU, wrap_failure, wrap_success
from .services.backup_svc import perform_backup, should_run_backup
from .services.metrics import (
    HealthMonitor,
    collect_metrics,
    metrics_summary,
    write_health_snapshot,
)
from .services.sysctl import check_failed_services
from .utils.format import human_datetime
from .utils.logging import get_logger, log_action, setup_logging

logger = get_logger(__name__)
_PROCESS_LOCK_FD: int | None = None
_PROCESS_LOCK_FD: int | None = None


async def health_check_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    monitor: HealthMonitor = context.bot_data["health_monitor"]
    disabled = context.bot_data.setdefault("alerts_disabled", {})

    metrics = collect_metrics(settings)
    failed_status = await check_failed_services(settings)
    failed_services = [status.name for status in failed_status if not status.is_healthy()]

    triggered, recovered = monitor.evaluate(metrics, failed_services)

    now = dt.datetime.now(dt.timezone.utc)

    def _is_disabled(code: str) -> bool:
        expiry_text = disabled.get(code)
        if not expiry_text:
            return False
        try:
            expiry = dt.datetime.fromisoformat(expiry_text)
        except ValueError:
            disabled.pop(code, None)
            return False
        if now >= expiry:
            disabled.pop(code, None)
            return False
        return True

    triggered = [alert for alert in triggered if not _is_disabled(alert.code)]

    write_health_snapshot(metrics, settings.health_file)

    if triggered:
        text_lines = [
            "⚠️ Alert server!",
            *(f"• {alert.message}" for alert in triggered),
            metrics_summary(metrics),
        ]
        await _broadcast(context, settings.admin_ids, "\n".join(text_lines))
        for alert in triggered:
            log_action(
                "alert.trigger",
                user_id=None,
                result="alert",
                detail=f"{alert.code}:{alert.message}",
            )

    if recovered:
        lines = ["✅ Recovery", *(f"• {code}" for code in recovered)]
        await _broadcast(context, settings.admin_ids, "\n".join(lines))
        for code in recovered:
            log_action("alert.recover", user_id=None, result="ok", detail=code)


async def backup_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    if not should_run_backup(settings):
        logger.info("Backup otomatis dilewati: snapshot terbaru masih valid")
        log_action("backup.auto", user_id=None, result="skip", detail="recent snapshot")
        return
    try:
        report = await perform_backup(settings)
        message = wrap_success(
            f"Backup otomatis selesai ({report.snapshot.name})."
        )
        await _broadcast(context, settings.admin_ids, message)
        log_action(
            "backup.auto",
            user_id=None,
            result="ok",
            detail=report.snapshot.name,
        )
    except Exception as exc:  # pragma: no cover - IO heavy
        error = wrap_failure(str(exc))
        await _broadcast(context, settings.admin_ids, error)
        log_action("backup.auto", user_id=None, result="fail", detail=str(exc))


async def _broadcast(
    context: ContextTypes.DEFAULT_TYPE, recipients: Iterable[int], text: str
) -> None:
    for chat_id in recipients:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning("Gagal kirim pesan ke %s: %s", chat_id, exc)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, Conflict):
        logger.warning("Telegram API conflict (kemungkinan bot sedang direstart)." )
        if context.application.running:
            await context.application.stop()
        return
    logger.error("Unhandled error processing update: %s", update, exc_info=err)


def _reschedule_backup_job(application: Application, time_str: str) -> None:
    hour, minute = map(int, time_str.split(":"))
    tzinfo = application.bot_data.get("tzinfo") or ZoneInfo("UTC")
    time_obj = dt.time(hour=hour, minute=minute, tzinfo=tzinfo)
    existing = application.bot_data.get("backup_job")
    if existing:
        existing.schedule_removal()
    job = application.job_queue.run_daily(backup_job, time=time_obj, name="backup-daily")
    application.bot_data["backup_job"] = job
    application.bot_data["backup_schedule"] = time_str
    logger.info("Backup job dijadwalkan ulang ke %s", time_str)


def build_application(settings: Settings) -> Application:
    tzinfo = ZoneInfo(settings.timezone)
    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=tzinfo)
    application = Application.builder().token(settings.bot_token).defaults(defaults).build()

    application.bot_data["settings"] = settings
    application.bot_data["tzinfo"] = tzinfo
    application.bot_data["health_monitor"] = HealthMonitor(settings.thresholds)
    application.bot_data["reschedule_backup_job"] = lambda value: _reschedule_backup_job(
        application, value
    )
    application.bot_data["backup_schedule"] = settings.backup_schedule

    application.add_handler(CommandHandler("start", start.start))
    application.add_handler(CommandHandler("help", start.help_command))
    application.add_handler(CommandHandler("status", start.status_command))

    application.add_handler(CommandHandler("svc", controls.service_command))
    application.add_handler(CommandHandler("svc_list", controls.control_menu))
    application.add_handler(CommandHandler("services", controls.control_menu))
    application.add_handler(CommandHandler("log_runtime", logs.log_runtime))
    application.add_handler(CommandHandler("log_errors", logs.log_errors))
    application.add_handler(CommandHandler("log_file", logs.log_file))
    application.add_handler(CommandHandler("log_journal", logs.log_journal))

    application.add_handler(CommandHandler("backup_now", backup.backup_now))
    application.add_handler(CommandHandler("backup_list", backup.backup_list))
    application.add_handler(CommandHandler("backup_verify", backup.backup_verify))

    application.add_handler(CommandHandler("ping", network.ping_command))
    application.add_handler(CommandHandler("speed", network.speed_command))
    application.add_handler(CommandHandler("tailscale", network.tailscale_command))

    application.add_handler(CommandHandler("apt_update", updates.apt_update))
    application.add_handler(CommandHandler("pip_sync", updates.pip_sync))
    application.add_handler(CommandHandler("git_pull", updates.git_pull))

    application.add_handler(CommandHandler("admins", admin.admins_list))
    application.add_handler(CommandHandler("set_backup", admin.set_backup_schedule))
    application.add_handler(CommandHandler("alerts", admin.alerts_status))
    application.add_handler(CommandHandler("alert_disable", admin.alert_disable))
    application.add_handler(CommandHandler("set_threshold", admin.set_threshold))
    application.add_handler(CommandHandler("svc_add", admin.service_add))
    application.add_handler(CommandHandler("svc_remove", admin.service_remove))
    application.add_handler(CommandHandler("uptime", monitoring.uptime_detail))

    application.add_handler(MessageHandler(filters.Regex("^📊 Status$"), monitoring.show_status))
    application.add_handler(MessageHandler(filters.Regex("^🧰 Kontrol$"), controls.control_menu))
    application.add_handler(MessageHandler(filters.Regex("^📜 Logs$"), logs.logs_menu))
    application.add_handler(MessageHandler(filters.Regex("^💾 Backup$"), backup.backup_menu))
    application.add_handler(MessageHandler(filters.Regex("^🌐 Network$"), network.network_menu))
    application.add_handler(MessageHandler(filters.Regex("^🔄 Update$"), updates.update_menu))
    application.add_handler(MessageHandler(filters.Regex("^⚙️ Settings$"), admin.settings_menu))

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)

    schedule_health_jobs(application)

    return application


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "Perintah belum dikenal. Gunakan menu tombol atau /help.", reply_markup=MAIN_MENU
        )


def schedule_health_jobs(application: Application) -> None:
    if application.job_queue is None:
        raise RuntimeError(
            "JobQueue tidak tersedia. Pastikan python-telegram-bot dipasang dengan ekstra 'job-queue'."
        )
    application.job_queue.run_repeating(health_check_job, interval=60, first=10)
    backup_time = application.bot_data.get("backup_schedule")
    if backup_time:
        _reschedule_backup_job(application, backup_time)


def main() -> None:
    settings = load_settings()
    _acquire_process_lock(settings.data_dir / ".bot.lock")
    setup_logging(settings.runtime_log, settings.actions_log)
    application = build_application(settings)

    logger.info("Bot mulai pada %s", human_datetime())
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()


def _acquire_process_lock(path: Path) -> None:
    global _PROCESS_LOCK_FD
    if _PROCESS_LOCK_FD is not None:
        return
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:  # pragma: no cover - file lock is platform specific
        os.close(fd)
        raise RuntimeError(
            "Instance bot lain masih berjalan. Matikan proses sebelumnya sebelum menjalankan ulang."
        ) from exc
    _PROCESS_LOCK_FD = fd
    atexit.register(_release_process_lock)


def _release_process_lock() -> None:
    global _PROCESS_LOCK_FD
    if _PROCESS_LOCK_FD is None:
        return
    try:
        fcntl.flock(_PROCESS_LOCK_FD, fcntl.LOCK_UN)
    finally:
        os.close(_PROCESS_LOCK_FD)
        _PROCESS_LOCK_FD = None
