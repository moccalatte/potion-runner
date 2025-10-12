"""Backup commands handlers."""
from __future__ import annotations

from html import escape
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from ..config import Settings
from ..menus import MAIN_MENU, PROCESSING, wrap_failure, wrap_success
from ..services.backup_svc import list_snapshots, perform_backup, verify_snapshot
from ..utils.logging import log_action


async def backup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Menu backup:\n"
        "• /backup_now → backup instan\n"
        "• /backup_list → daftar snapshot\n"
        "• /backup_verify &lt;manifest&gt; → verifikasi checksum"
    )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)
    log_action("backup.menu", user_id=update.effective_user.id, result="ok", detail="menu")


async def backup_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not settings.is_admin(user_id):
        await update.message.reply_text("Fitur ini hanya untuk admin.")
        log_action("backup.now", user_id=user_id, result="deny", detail="not admin")
        return

    pending = await update.message.reply_text(PROCESSING)
    try:
        report = await perform_backup(settings)
        summary = (
            f"Snapshot {report.snapshot.name} selesai. {report.files_indexed} file diindeks."
        )
        await pending.edit_text(wrap_success(summary))
        log_action("backup.now", user_id=user_id, result="ok", detail=summary)
    except Exception as exc:  # pragma: no cover - IO heavy
        await pending.edit_text(wrap_failure(str(exc)))
        log_action("backup.now", user_id=user_id, result="fail", detail=str(exc))


async def backup_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    snapshots = list_snapshots(settings)
    if not snapshots:
        await update.message.reply_text("Belum ada snapshot.")
        return
    lines = ["Daftar snapshot tersedia:"]
    for snap in snapshots[-10:]:
        manifest = settings.manifests_dir / f"{snap.name}.json"
        status = "✅" if manifest.exists() else "⚪"
        lines.append(f"{status} {escape(snap.name)}")
    await update.message.reply_text("\n".join(lines))
    log_action("backup.list", user_id=update.effective_user.id, result="ok", detail="list")


async def backup_verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.bot_data["settings"]
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "Gunakan /backup_verify &lt;manifest&gt;. Contoh: /backup_verify 20240101-010101.json"
        )
        return
    manifest_name = context.args[0]
    manifest_path = settings.manifests_dir / manifest_name
    if not manifest_path.exists():
        await update.message.reply_text("Manifest tidak ditemukan.")
        return
    pending = await update.message.reply_text(PROCESSING)
    mismatches = await verify_snapshot(manifest_path)
    if mismatches:
        await pending.edit_text(wrap_failure("\n".join(mismatches[:30])))
        log_action("backup.verify", user_id=user_id, result="fail", detail="mismatch")
    else:
        await pending.edit_text(wrap_success("Semua checksum cocok."))
        log_action("backup.verify", user_id=user_id, result="ok", detail=manifest_name)


__all__ = ["backup_menu", "backup_now", "backup_list", "backup_verify"]
