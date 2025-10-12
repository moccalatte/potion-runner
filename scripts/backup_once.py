#!/usr/bin/env python3
"""Run a single backup snapshot via command line."""
import argparse
import asyncio

from app.config import load_settings
from app.services.backup_svc import perform_backup, should_run_backup
from app.utils.logging import setup_logging


async def main(force: bool) -> None:
    settings = load_settings()
    setup_logging(settings.runtime_log, settings.actions_log)
    if not force and not should_run_backup(settings):
        print("Backup dilewati: snapshot terbaru masih dalam rentang aman.")
        return
    report = await perform_backup(settings)
    print(f"Backup selesai: {report.snapshot} -> manifest {report.manifest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jalankan backup potion-runner sekali.")
    parser.add_argument("--force", action="store_true", help="Tetap jalankan walau ada backup terbaru.")
    args = parser.parse_args()
    asyncio.run(main(args.force))
